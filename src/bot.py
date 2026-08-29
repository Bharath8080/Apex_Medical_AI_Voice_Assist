import asyncio
import datetime
import json
import sys
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
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.groq.stt import GroqSTTService
from pipecat.services.tts_service import TextAggregationMode
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

from src import config, rag_engine, calcom_engine

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


from pydantic import BaseModel
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


class TranscriptBroadcaster(FrameProcessor):
    """Transmits live user STT, bot streaming text, and state synchronization directly to the UI."""

    def __init__(self, websocket):
        super().__init__()
        self._ws = websocket

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, InterimTranscriptionFrame):
            if frame.text and frame.text.strip():
                await self._send(UserTranscriptPayload(text=frame.text.strip(), final=False))
        elif isinstance(frame, TranscriptionFrame):
            if frame.text and frame.text.strip():
                await self._send(UserTranscriptPayload(text=frame.text.strip(), final=True))
                await self._send(BotStatePayload(state="thinking"))
        elif isinstance(frame, TextFrame):
            if frame.text:
                await self._send(BotTranscriptPayload(text=frame.text))
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
    transport = FastAPIWebsocketTransport(
        websocket=websocket_client,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
            turn_analyzer=LocalSmartTurnAnalyzerV3(),
            serializer=FastAPIRealtimeSerializer(),
            audio_in_sample_rate=16000,
            audio_out_sample_rate=24000,
        ),
    )

    # 1. STT with 3-Tier Failover
    elevenlabs_stt = ElevenLabsRealtimeSTTService(
        api_key=config.ELEVENLABS_API_KEY,
        settings=ElevenLabsRealtimeSTTService.Settings(
            model="scribe_v2_realtime",
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
        services=[elevenlabs_stt, groq_stt, deepgram_stt],
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
            payload = json.dumps({
                "type": "tool_call",
                "toolPart": {
                    "type": name,
                    "state": state,
                    "input": input_data,
                    "output": output_data,
                }
            })
            asyncio.run_coroutine_threadsafe(websocket_client.send_text(payload), loop)
        except Exception:
            pass

    @tool
    def rag_search(query: str) -> str:
        """Search Apex Care Hospital's knowledge base: visiting hours, test prep, insurance, policies, prescriptions."""
        notify_tool("rag_search", "input-streaming", {"query": query})
        res = rag_engine.retrieve_context(query, top_k=3)
        notify_tool("rag_search", "output-available", {"query": query}, res)
        return res

    os.environ.setdefault("TAVILY_API_KEY", config.TAVILY_API_KEY)
    tavily_search = TavilySearch(max_results=3, search_depth="basic")

    @tool
    def web_search(query: str) -> str:
        """Search the internet for real-time medical info not found in the hospital guide."""
        notify_tool("web_search", "input-streaming", {"query": query})
        res = tavily_search.invoke(query)
        res_str = str(res)
        notify_tool("web_search", "output-available", {"query": query}, res_str)
        return res_str

    @tool
    def check_available_slots(start_time: str = "", end_time: str = "") -> str:
        """Check open doctor consultation slots on Cal.com. Optional ISO 8601 start_time and end_time."""
        notify_tool("check_available_slots", "input-streaming", {"start": start_time, "end": end_time})
        res = calcom_engine.get_available_slots(start_time, end_time)
        notify_tool("check_available_slots", "output-available", {"start": start_time, "end": end_time}, res)
        return res

    @tool
    def book_appointment(start_time: str, name: str, email: str, time_zone: str = "Asia/Kolkata") -> str:
        """Book a doctor appointment on Cal.com once patient agrees on a slot and provides their full name and email."""
        notify_tool("book_appointment", "input-streaming", {"start": start_time, "name": name, "email": email})
        res = calcom_engine.book_appointment(start_time, name, email, time_zone)
        notify_tool("book_appointment", "output-available", {"start": start_time, "name": name, "email": email}, res)
        return res

    current_time_str = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    system_prompt = (
        f"Today's date and time is {current_time_str}.\n"
        "You are the warm, professional AI Medical Receptionist for Apex Care Hospital.\n"
        "You have access to 4 tools:\n"
        "1. rag_search: Search internal hospital policies, visiting hours, test prep, insurance.\n"
        "2. web_search: Search the internet for general medical info or drug questions.\n"
        "3. check_available_slots: Fetch open doctor appointment slots on Cal.com.\n"
        "4. book_appointment: Confirm a booking on Cal.com using start_time (ISO 8601), name, and email.\n\n"
        "Appointment Scheduling Flow:\n"
        "- When a patient asks to book an appointment (e.g., 'for tomorrow' or 'next Monday'), resolve the exact date using today's date and call check_available_slots to find open timings.\n"
        "- Suggest 2-3 specific time options to the caller.\n"
        "- Once the patient chooses a slot, ask for their full name and email address.\n"
        "- Confirm the email back to the patient to ensure voice transcription accuracy before calling book_appointment.\n\n"
        "Clinical Safety Rules:\n"
        "- Never diagnose conditions, interpret lab results, or suggest medication dosages.\n"
        "- For emergencies (chest pain, stroke, breathing difficulty), advise calling 911 immediately.\n"
        "- Keep responses concise and natural for voice — 1 to 2 spoken sentences, no markdown or special symbols."
    )

    agent = create_react_agent(
        model=groq_llm,
        tools=[rag_search, web_search, check_available_slots, book_appointment],
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )

    def agent_chain(x):
        query = str(x.get("input", "") or "") if isinstance(x, dict) else str(x)
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": "apex-session-1"}},
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
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    user_transcripts = TranscriptBroadcaster(websocket_client)
    bot_transcripts = TranscriptBroadcaster(websocket_client)

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
        logger.info("Client connected to Voice Pipeline via FastAPI WebSocket.")
        greeting = "Hello! Thank you for calling Apex Care Medical Center. I am your AI receptionist. How can I help you today?"
        await bot_transcripts.process_frame(TextFrame(text=greeting), FrameDirection.DOWNSTREAM)

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected from voice pipeline.")
        await task.queue_frames([EndFrame()])

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
