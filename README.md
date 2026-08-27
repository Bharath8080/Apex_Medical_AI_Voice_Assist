# 🏥 Apex Health — Real-Time Medical Voice Assistant & RAG Pipeline

A production-grade, low-latency conversational voice assistant for hospital reception, patient triage, and clinical guidance. Built with **Pipecat AI 1.8.0**, **FastAPI WebSockets**, **Groq LLM**, **ElevenLabs / Deepgram / Cartesia TTS**, **ChromaDB Vector RAG**, and an interactive **3D Orb React Frontend**.

---

## ⚡ Key Architecture & Features

### 1. 🎙️ Real-Time Voice Streaming Pipeline (Pipecat AI 1.8.0)
* **Audio In/Out**: 16kHz 16-bit Mono PCM streamed bi-directionally over WebSockets.
* **VAD (Voice Activity Detection)**: **Silero VAD** with automatic natural barge-in / speech interruption.
* **STT (Speech-to-Text)**: **Deepgram Nova-2** real-time streaming transcription.
* **LLM Engine**: **Groq** (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) with LangChain LCEL streaming.

### 2. 🔄 3-Tier Automatic TTS Failover
Zero-downtime voice delivery with intelligent failover fallback:
1. **Primary**: **ElevenLabs** (`eleven_flash_v2_5` — ultra-realistic conversational voice)
2. **Secondary Fallback**: **Deepgram** (`aura-helios-en` / `flux` streaming)
3. **Tertiary Fallback**: **Cartesia** (`sonic-english`)

### 3. 📚 ChromaDB Vector RAG Engine
* **Vector Store**: **ChromaDB** (`chroma_db/`) dense vector database.
* **Embeddings**: **FastEmbed** (`BAAI/bge-base-en-v1.5` — lightweight, fast, local CPU embeddings).
* **Chunking**: `chunk_size=800`, `chunk_overlap=200`.
* **Knowledge Base**: 10-page comprehensive **`data/guide.pdf`** covering 25 hospital policy sections:
  * Inpatient & ICU visiting hours
  * Fasting & diagnostic test preparation protocols (Ultrasound, CT contrast, MRI, Endoscopy)
  * Patient intake, registration, and specialist referral rules
  * Insurance verification, TPA cashless pre-authorization, and No Surprises Act Good Faith Estimates
  * Prescription refills & Schedule II–IV controlled substance policies
  * Clinical safety boundaries & Red-flag emergency triage escalation

### 4. 🌐 Real-Time Clinical Web Search (Keenable AI)
* Integrated with Pipecat's native **KeenableWebSearch** service for live web page searches regarding drug side effects, contraindications, and external clinical queries.

### 5. 🎨 Minimalist 3D Orb Voice Interface
* **Single Viewport UI**: Clean, responsive layout inspired by modern voice AI applications.
* **3D Audio Reactive Orb**: Visualizes agent states in real-time (*Listening, Thinking, Speaking, Idle*).
* **Live Transcript Drawer**: Real-time streaming conversation bubbles with text input & message clearing.
* **Theme Customizer**: 5 clinical accent colors (*Indigo, Cyan, Emerald, Purple, Orange*) + Dark/Light mode toggle.

---

## 📁 Project Structure

```text
├── data/
│   └── guide.pdf                  # 10-page static hospital knowledge base PDF
├── chroma_db/                     # ChromaDB persistent vector database
├── frontend/                      # React + Tailwind + Vite single-screen UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── agents-ui/         # Control bar & chat transcript drawer
│   │   │   └── ui/                # 3D WebGL Audio Orb & Shimmering Text
│   │   ├── hooks/
│   │   │   └── useVoiceAgent.js   # WebSocket audio streaming & Web Audio hook
│   │   ├── App.jsx                # Main minimal single-screen voice interface
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   └── gen_info.py                # Generates the 10-page guide.pdf
├── src/
│   ├── bot.py                     # Pipecat pipeline, STT, LLM chain, TTS failover
│   ├── config.py                  # Pydantic environment configuration
│   └── rag_engine.py              # ChromaDB vector store, FastEmbed, and RAG retrieval
├── main.py                        # FastAPI server hosting WebSocket /ws & static bundle
├── pyproject.toml
└── .env                           # API keys & configuration
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Python 3.10+** (recommended: `uv` or `venv`)
* **Node.js 18+** & **npm**

---

### 2. Environment Configuration
Create a `.env` file in the project root:

```ini
# Deepgram (STT & TTS fallback)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Groq (Fast LLM Inference)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# ElevenLabs (Primary TTS)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL_ID=eleven_flash_v2_5

# Cartesia (Tertiary TTS Fallback)
CARTESIA_API_KEY=your_cartesia_api_key
CARTESIA_VOICE_ID=248be419-c632-4f23-adf1-5324ed7dbf10

# Keenable (Real-Time Web Search)
KEENABLE_API_KEY=your_keenable_api_key

# Server
HOST=127.0.0.1
PORT=8000
```

---

### 3. Generate & Ingest the Hospital Knowledge Base (RAG)

```bash
# 1. Generate the 10-page guide.pdf
uv run python scripts/gen_info.py

# 2. Ingest guide.pdf into ChromaDB
uv run python -m src.rag_engine
```

---

### 4. Build the Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

---

### 5. Launch the Server

```bash
uv run python main.py
```

Open your browser at **`http://127.0.0.1:8000`** and click the **Start Consultation** button to begin speaking in real time!

For active frontend development with hot-reloading:
```bash
cd frontend
npm run dev
```

---

## 🧪 Sample Voice Questions to Test

| Topic | Example Question |
| :--- | :--- |
| **Visiting Hours** | *"What are the visiting hours for the General Ward and ICU?"* |
| **Test Preparation** | *"What preparation do I need before an Abdominal Ultrasound or Lipid test?"* |
| **Specialist Referral** | *"Can I see a Cardiologist without a referral from my primary doctor?"* |
| **Late Arrivals** | *"What happens if I arrive 20 minutes late for my appointment?"* |
| **Prescription Refills** | *"How do I request a refill for my blood pressure medication?"* |
| **No-Show Policy** | *"What is the hospital penalty if I miss my scheduled appointment?"* |
| **Emergency Triage** | *"What should I do if someone has severe chest pain or stroke symptoms?"* |

---

## 📜 License
MIT License. Created with **Pipecat AI**, **FastAPI**, and **LangChain**.
