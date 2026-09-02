import asyncio
import datetime
import json
import sys
import uuid
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import (
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    EndFrame,
    Frame,
    InputAudioRawFrame,
    InterimTranscriptionFrame,
    OutputAudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    TTSSpeakFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.service_switcher import ServiceSwitcher, ServiceSwitcherStrategyFailover
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.flux.tts import DeepgramFluxTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.elevenlabs.stt import CommitStrategy, ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.groq.stt import GroqSTTService
from pipecat.services.tts_service import TextAggregationMode
from pipecat.transcriptions.language import Language
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
from pipecat.processors.frameworks.langchain import LangchainProcessor
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import os

from src import config, rag_engine, cal, db

logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    filter=lambda record: "emitting as passthrough" not in record["message"],
)


class FastAPIRealtimeSerializer(FrameSerializer):
    """Serializes outgoing raw PCM audio bytes and deserializes incoming PCM audio or text."""

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, OutputAudioRawFrame):
            return frame.audio
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes):
            return InputAudioRawFrame(
                audio=data,
                num_channels=1,
                sample_rate=16000,
            )
        if isinstance(data, str) and data.strip():
            return TranscriptionFrame(
                text=data.strip(),
                user_id="user",
                timestamp="",
                finalized=True,
            )
        return None


from pydantic import BaseModel, Field
from typing import Literal


class UserTranscriptPayload(BaseModel):
    type: Literal["user_transcript"] = "user_transcript"
    text: str
    final: bool


class BotTranscriptPayload(BaseModel):
    type: Literal["bot_transcript"] = "bot_transcript"
    text: str


class BotStatePayload(BaseModel):
    type: Literal["bot_state"] = "bot_state"
    state: str


class ToolPart(BaseModel):
    type: str
    state: str
    input: dict = Field(default_factory=dict)
    output: str = ""


class ToolCallPayload(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    toolPart: ToolPart


class TranscriptBroadcaster(FrameProcessor):
    """Transmits live user STT, bot streaming text, and state synchronization directly to the UI."""

    def __init__(self, websocket, session_history: list | None = None):
        super().__init__()
        self._ws = websocket
        self._history = session_history if session_history is not None else []

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, InterimTranscriptionFrame):
            if frame.text and frame.text.strip():
                await self._send(UserTranscriptPayload(text=frame.text.strip(), final=False))
        elif isinstance(frame, TranscriptionFrame):
            if frame.text and frame.text.strip():
                await self._send(UserTranscriptPayload(text=frame.text.strip(), final=True))
                await self._send(BotStatePayload(state="thinking"))
                self._history.append({"role": "user", "text": frame.text.strip()})
        elif isinstance(frame, (TextFrame, TTSSpeakFrame)):
            if frame.text:
                await self._send(BotTranscriptPayload(text=frame.text))
                self._history.append({"role": "assistant", "text": frame.text.strip()})
        elif isinstance(frame, BotStartedSpeakingFrame):
            await self._send(BotStatePayload(state="speaking"))
        elif isinstance(frame, BotStoppedSpeakingFrame):
            await self._send(BotStatePayload(state="listening"))
        elif isinstance(frame, UserStartedSpeakingFrame):
            await self._send(BotStatePayload(state="listening"))

        await self.push_frame(frame, direction)

    async def _send(self, payload: BaseModel):
        try:
            await self._ws.send_text(payload.model_dump_json())
        except Exception:
            pass



async def run_bot(websocket_client):
    vad = SileroVADAnalyzer(
        params=VADParams(
            confidence=0.7,
            start_secs=0.2,
            stop_secs=0.8,
            min_volume=0.6,
        )
    )
    turn_analyzer = LocalSmartTurnAnalyzerV3()

    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=vad,
            turn_analyzer=turn_analyzer,
            serializer=FastAPIRealtimeSerializer(),
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
        ),
    )


    # 1. STT with 3-Tier Failover
    elevenlabs_stt = ElevenLabsRealtimeSTTService(
        api_key=config.ELEVENLABS_API_KEY,
        commit_strategy=CommitStrategy.VAD,
        settings=ElevenLabsRealtimeSTTService.Settings(
            model="scribe_v2_realtime",
            language=Language.EN,
            filter_background_audio=True,
            vad_silence_threshold_secs=0.8,
            vad_threshold=0.4,
        ),
    )

    groq_stt = GroqSTTService(
        api_key=config.GROQ_API_KEY,
        settings=GroqSTTService.Settings(
            model=config.GROQ_STT_MODEL,
        ),
    )

    deepgram_stt = DeepgramSTTService(
        api_key=config.DEEPGRAM_API_KEY,
        settings=DeepgramSTTService.Settings(
            model="nova-3",
            interim_results=True,
        ),
    )

    stt_switcher = ServiceSwitcher(
        services=[elevenlabs_stt, deepgram_stt, groq_stt],
        strategy_type=ServiceSwitcherStrategyFailover,
    )

    # 2. LLM + LangGraph ReAct Agent with 2 Tools: RAG & Web Search
    groq_llm = ChatGroq(
        model=config.GROQ_MODEL,
        groq_api_key=config.GROQ_API_KEY,
        temperature=config.LLM_TEMPERATURE,
    )

    loop = asyncio.get_running_loop()

    def notify_tool(name: str, state: str, input_data: dict, output_data: str = ""):
        try:
            payload = ToolCallPayload(
                toolPart=ToolPart(
                    type=name,
                    state=state,
                    input=input_data,
                    output=output_data,
                )
            )
            asyncio.run_coroutine_threadsafe(
                websocket_client.send_text(payload.model_dump_json()),
                loop,
            )
        except Exception:
            pass


    @tool
    def rag_search(query: str) -> str:
        """Search the Apex Care Hospital Knowledge Base for hospital services, visiting hours, operating hours, policies, insurance, intake forms, and amenities."""
        notify_tool("rag_search", "input-streaming", {"query": query})
        res = rag_engine.retrieve_context(query, top_k=3)
        notify_tool("rag_search", "output-available", {"query": query}, res)
        return res

    os.environ.setdefault("TAVILY_API_KEY", config.TAVILY_API_KEY)
    tavily_search = TavilySearch(max_results=3, search_depth="basic")

    @tool
    def web_search(query: str) -> str:
        """Search the web for general medical topics, symptoms, medications, drug interactions, diseases, treatments, home remedies, recovery advice, and health information not specific to hospital policies."""
        notify_tool("web_search", "input-streaming", {"query": query})
        res = tavily_search.invoke(query)
        res_str = str(res)
        notify_tool("web_search", "output-available", {"query": query}, res_str)
        return res_str

    @tool
    def check_available_slots(start_time: str = "", end_time: str = "") -> str:
        """Check open doctor consultation slots on Cal.com. Optional ISO 8601 start_time and end_time."""
        notify_tool("check_available_slots", "input-streaming", {"start": start_time, "end": end_time})
        res = cal.get_available_slots(start_time, end_time)
        notify_tool("check_available_slots", "output-available", {"start": start_time, "end": end_time}, res)
        return res

    @tool
    def book_appointment(
        start_time: str,
        name: str,
        email: str,
        phone_number: str = "",
        insurance_provider: str = "",
        reason_for_visit: str = "",
        time_zone: str = "Asia/Kolkata",
    ) -> str:
        """Book a doctor appointment on Cal.com with patient intake details (phone, insurance, reason for visit)."""
        notify_tool("book_appointment", "input-streaming", {"start": start_time, "name": name, "email": email})
        res = cal.book_appointment(start_time, name, email, phone_number, insurance_provider, reason_for_visit, time_zone)
        notify_tool("book_appointment", "output-available", {"start": start_time, "name": name, "email": email}, res)
        return res

    current_time_str = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    system_prompt = (
        f"Today's date and time is {current_time_str}.\n"
        "You are the warm, professional AI Medical Receptionist for Apex Care Hospital.\n\n"
        "VOICE RECEPTIONIST CONVERSATION RULES (CRITICAL):\n"
        "- ALWAYS keep your spoken response strictly to 1 to 2 short, natural sentences.\n"
        "- NEVER repeat or rephrase a question twice in the same response. Ask each question only ONCE.\n"
        "- Be direct, warm, and concise. Never give long explanations, paragraphs, or essay-like responses.\n"
        "- NEVER use bullet points, numbered lists, markdown (*, _, #), or parenthesis.\n"
        "- NEVER repeat dates or times multiple times. Summarize tool outputs in 1-2 clear spoken lines.\n\n"
        "GREETINGS & CASUAL CHIT-CHAT (DO NOT CALL ANY TOOLS):\n"
        "- You have ALREADY welcomed the caller at the start of the call. If the caller replies with a plain greeting (like 'Hi', 'Hello', 'Good morning', 'Hey'), DO NOT repeat the welcome intro or hospital name! Acknowledge warmly and ask how you can assist, for example: 'Hello! How can I help you today?'\n"
        "- If the caller checks your presence or status (like 'Are you there?', 'Are you still active?', 'Hello?', 'Can you hear me?', 'Are you listening?'), respond naturally and reassuringly in one sentence — confirm you are present and ready, for example: 'Yes, I am here! How can I help you?' or 'Absolutely, still with you! What can I do for you?'\n"
        "- For any casual, conversational, or off-topic message that is not a medical or hospital question, respond naturally in one short sentence using your own judgment. Do NOT default to a scripted welcome line. Stay warm, human, and relevant to what was just said.\n"
        "- If the caller says thank you or goodbye, reply warmly in one sentence without calling tools.\n\n"
        "STRICT APPOINTMENT INTAKE STATE MACHINE (MANDATORY: ONE STEP PER TURN):\n"
        "Turn 1 - Offer Available Slots ONLY:\n"
        "  When the caller asks about scheduling, call check_available_slots.\n"
        "  Respond ONLY with: 'We have openings tomorrow at [time 1], [time 2], or [time 3]. Which of these times works best for you?'\n"
        "  STOP IMMEDIATELY! DO NOT ask for name, email, or any other details in this turn.\n\n"
        "Turn 2 - Ask Name & Email ONLY:\n"
        "  After the caller chooses their preferred time, respond ONLY with: 'Great! Could you please share your full name and email address?'\n"
        "  STOP IMMEDIATELY! DO NOT ask for insurance or phone number yet.\n\n"
        "Turn 3 - Ask Insurance Provider & Phone Number ONLY:\n"
        "  After the caller gives their name and email, respond with: 'Thank you. What is your insurance provider and mobile phone number?'\n"
        "  STOP IMMEDIATELY! Ask this question only once. DO NOT repeat, rephrase, or ask for symptoms yet.\n\n"
        "Turn 4 - Confirm Symptoms / Reason for Visit:\n"
        "  After the caller provides their insurance and phone number, check conversation memory:\n"
        "  - If symptoms were mentioned earlier (e.g., headache, back pain), ask for confirmation: 'I have your reason noted as [symptom]—is that correct, or do you have any other symptoms?'\n"
        "  - If no symptoms were mentioned earlier, ask: 'Could you please share the primary reason or symptoms for your visit today?'\n"
        "  STOP IMMEDIATELY! DO NOT call book_appointment yet until they confirm or provide their reason.\n\n"
        "Turn 5 - Cross-Check & Confirm Booking:\n"
        "  Once the reason is confirmed or updated, call book_appointment.\n"
        "  Respond with a single confirmation sentence summarizing the booking.\n\n"
        "TOOL USAGE RULES (ALWAYS CALL TOOLS FOR FACTUAL & MEDICAL INQUIRIES):\n"
        "- web_search: Call this for ANY general medical question, symptoms, medications, drug interactions, disease overviews, home remedies, recovery times, or health questions. Summarize the result briefly in 1-2 sentences. ONLY append 'Would you like to schedule an appointment with one of our doctors for that?' if the caller is asking about their OWN symptoms or a health concern they are personally experiencing. DO NOT add an appointment offer for general medical facts, definitions, or informational questions.\n"
        "- rag_search: Call this for ANY question about Apex Care Hospital's official policies, facilities, services, or procedures. Always use rag_search when the caller asks about:\n"
        "  * Operating hours (outpatient clinics, emergency department, 24/7 pharmacy, telehealth hours)\n"
        "  * Patient registration and intake forms (Form G-101 consent, Form H-202 history, Form P-303 HIPAA, Form F-404 financial)\n"
        "  * Doctor referral requirements vs direct booking departments\n"
        "  * Check-in rules, 15-minute late arrival grace period, standby queue, and cancellation or no-show policies\n"
        "  * Accepted insurance plans, billing terms, co-pays, and financial assistance or hardship payment plans\n"
        "  * Preparation instructions for diagnostic tests (fasting blood tests, ultrasounds, MRI, CT scans, mammography, endoscopy)\n"
        "  * Medical records release (Form R-10), lab report turnaround times, and digital patient portal\n"
        "  * Inpatient admissions, self-pay deposits, ward visiting hours, and discharge checkout times\n"
        "  * Campus amenities, parking garage fees and validation rules, wheelchair assistance, and prayer room\n"
        "  * Patient rights, Patient Ombudsman, language interpretation services (40+ languages), and accessibility accommodations\n"
        "  * Telehealth eligibility criteria and virtual visit guidelines\n"
        "  Answer factually in 1-2 concise sentences strictly from the retrieved context. DO NOT append any appointment booking offer after hospital knowledge queries unless the caller explicitly asks about booking.\n"
        "- check_available_slots: Checking open doctor appointment slots on Cal.com.\n"
        "- book_appointment: Confirming a booking on Cal.com.\n\n"
        "Clinical Safety Rules:\n"
        "- Never diagnose conditions, interpret lab values, or prescribe medication dosages.\n"
        "- For medical emergencies (chest pain, stroke, severe breathing difficulty), advise calling 911 immediately."
    )




    agent = create_react_agent(
        model=groq_llm,
        tools=[
            rag_search,
            web_search,
            check_available_slots,
            book_appointment,
        ],
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    session_thread_id = str(uuid.uuid4())

    def agent_chain(x):
        query = str(x.get("input", "") or "") if isinstance(x, dict) else str(x)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": session_thread_id}},
        )
        return result["messages"][-1].content


    langchain_processor = LangchainProcessor(chain=RunnableLambda(agent_chain))

    # 3. TTS with Failover (1st: ElevenLabs, 2nd: Deepgram Fallback, 3rd: Cartesia)
    elevenlabs_tts = ElevenLabsTTSService(
        api_key=config.ELEVENLABS_API_KEY,
        sample_rate=24000,
        settings=ElevenLabsTTSService.Settings(
            voice=config.ELEVENLABS_VOICE_ID,
            model=config.ELEVENLABS_MODEL_ID,
        ),
    )

    deepgram_tts = DeepgramFluxTTSService(
        api_key=config.DEEPGRAM_API_KEY,
        sample_rate=24000,
        text_aggregation_mode=TextAggregationMode.TOKEN,
        settings=DeepgramFluxTTSService.Settings(voice=config.DEEPGRAM_VOICE),
    )

    cartesia_tts = CartesiaTTSService(
        api_key=config.CARTESIA_API_KEY,
        sample_rate=24000,
        settings=CartesiaTTSService.Settings(
            voice=config.DEFAULT_VOICE_ID,
            model=config.CARTESIA_MODEL_ID,
        ),
    )

    tts_switcher = ServiceSwitcher(
        services=[elevenlabs_tts, deepgram_tts, cartesia_tts],
        strategy_type=ServiceSwitcherStrategyFailover,
    )

    # Empty context - no system message here, the RAG prompt is the only one
    context = LLMContext([])
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=vad),
    )


    session_history = []
    user_transcripts = TranscriptBroadcaster(websocket_client, session_history)
    bot_transcripts = TranscriptBroadcaster(websocket_client, session_history)

    pipeline = Pipeline(
        [
            transport.input(),
            stt_switcher,
            user_transcripts,
            user_aggregator,
            langchain_processor,
            bot_transcripts,
            tts_switcher,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected.")
        greeting = "Hi there, welcome to Apex Medical Care Center! How may I help you today?"
        await bot_transcripts.process_frame(TTSSpeakFrame(text=greeting), FrameDirection.DOWNSTREAM)


    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected.")
        await task.queue_frames([EndFrame()])
        if session_history:
            asyncio.create_task(asyncio.to_thread(db.extract_and_log_call, session_history))

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)

