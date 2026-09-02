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
        """Search Apex Care Hospital knowledge base: visiting hours, operating hours & 24/7 pharmacy, diagnostic test prep, accepted insurance & billing, patient intake forms, referral requirements, late arrivals & cancellation policies, inpatient admission deposits, medical records turnaround, telehealth eligibility, parking & amenities, patient rights & language interpretation."""
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
        "- Be direct, warm, and concise. Never give long explanations, paragraphs, or essay-like responses.\n"
        "- NEVER use bullet points, numbered lists, markdown (*, _, #), or parenthesis.\n"
        "- NEVER repeat dates or times multiple times. Summarize tool outputs in 1-2 clear spoken lines.\n\n"
        "GREETINGS & CASUAL CHIT-CHAT (DO NOT CALL ANY TOOLS):\n"
        "- You have ALREADY welcomed the caller at the start of the call. If the caller replies with a greeting (like 'Hi', 'Hello', 'Good morning', 'Hey'), DO NOT repeat the welcome intro or hospital name! Acknowledge warmly and ask how you can assist them in one sentence, for example: 'Hello! Are you looking to schedule an appointment with one of our doctors, or do you have a question about our services or symptoms?'\n"
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
        "  After the caller gives their name and email, respond ONLY with: 'Thank you. Could you please provide your insurance provider and mobile phone number?'\n"
        "  STOP IMMEDIATELY! DO NOT ask for symptoms or reason yet.\n\n"
        "Turn 4 - Confirm Symptoms / Reason for Visit:\n"
        "  After the caller provides their insurance and phone number, check conversation memory:\n"
        "  - If symptoms were mentioned earlier (e.g., headache, back pain), ask for confirmation: 'I have your reason noted as [symptom]—is that correct, or do you have any other symptoms?'\n"
        "  - If no symptoms were mentioned earlier, ask: 'Could you please share the primary reason or symptoms for your visit today?'\n"
        "  STOP IMMEDIATELY! DO NOT call book_appointment yet until they confirm or provide their reason.\n\n"
        "Turn 5 - Cross-Check & Confirm Booking:\n"
        "  Once the reason is confirmed or updated, call book_appointment.\n"
        "  Respond with a single confirmation sentence summarizing the booking.\n\n"
        "TOOL USAGE RULES (ALWAYS CALL TOOLS FOR FACTUAL & MEDICAL INQUIRIES):\n"
        "- web_search: Call this for ANY general medical question, symptoms, medications, drug interactions, disease overviews, home remedies, recovery times, or health questions. Always perform a web search to provide accurate medical facts, summarize briefly in 1-2 sentences, and append a short closing offer: 'Would you like to schedule an appointment with one of our doctors for that?'\n"
        "- rag_search: Call this for ANY Apex Care Hospital specific query: visiting hours (General Wards/ICU/NICU/Maternity), clinic hours, 24/7 pharmacy, patient intake & forms (G-101, H-202, P-303, F-404), specialist referral rules, check-in & late arrival policies, cancellation fees, accepted insurance plans, co-pays & hardship plans, diagnostic test prep, medical records & portal, admission deposits & checkout, parking fees & validation, telehealth eligibility, patient rights, and language interpretation.\n"
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

