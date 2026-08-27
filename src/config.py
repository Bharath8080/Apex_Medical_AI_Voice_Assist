import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()
ELEVENLABS_API_KEY = (os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY", "")).strip()
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "").strip()

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
