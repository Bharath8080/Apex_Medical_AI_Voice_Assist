import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY", "")
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
CALCOM_API_KEY = os.getenv("CALCOM_API_KEY")
CALCOM_EVENT_TYPE_ID = int(os.getenv("CALCOM_EVENT_TYPE_ID"))
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# Groq STT & LLM
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# TTS Models & Voices
DEEPGRAM_VOICE = os.getenv("DEEPGRAM_VOICE", "flux-brittany-en")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
DEFAULT_VOICE_ID = os.getenv("CARTESIA_VOICE_ID", "e07c00bc-4134-4eae-9ea4-1a55fb45746b")
CARTESIA_MODEL_ID = os.getenv("CARTESIA_MODEL_ID", "sonic-latest")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

