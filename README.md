# Project Mentor AI

A JARVIS-inspired AI assistant with full system control, proactive mentoring, voice interaction, and multi-agent intelligence.

![Stack](https://img.shields.io/badge/Next.js-14-black) ![Stack](https://img.shields.io/badge/FastAPI-Python-blue) ![Stack](https://img.shields.io/badge/Gemini-2.0-orange) ![Stack](https://img.shields.io/badge/ChromaDB-RAG-green)

## Features

- **Proactive Greeting** — Time-aware welcome when you open the app
- **Voice Control** — Web Speech API with "Hey Mentor" / "Jarvis" wake words
- **System Control** — Open apps, browse web, run commands, screenshots, lock PC
- **Multi-Agent AI** — LangGraph routes to CTO, PM, Marketing, VC, and Mentor agents
- **RAG Pipeline** — ChromaDB indexes your `knowledge/` folder automatically
- **Long-Term Memory** — Firestore (with local JSON fallback for dev)
- **Real-Time** — WebSocket for instant command execution
- **Holographic UI** — Glassmorphism, particles, Framer Motion animations

## Project Structure

```
project-mentor-ai/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── agents/          # LangGraph multi-agent system
│   │   ├── routers/         # API & WebSocket routes
│   │   ├── services/        # Gemini, RAG, Memory, System Control
│   │   ├── config.py
│   │   ├── models.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Next.js 14 frontend
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   ├── components/      # UI components
│   │   ├── hooks/           # WebSocket & Voice hooks
│   │   └── lib/             # API client
│   └── Dockerfile
├── knowledge/               # RAG knowledge base (Markdown)
├── deploy/                  # Cloud Run deployment scripts
└── docker-compose.yml
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### 1. Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000** — you should hear: *"Good [morning/afternoon/evening], Sir. How can I help you today, sir?"*

## Voice Commands

| Command | Action |
|---------|--------|
| "Open Chrome" | Launch Chrome browser |
| "Open VS Code" | Launch Visual Studio Code |
| "Open Terminal" | Open command prompt |
| "Open Spotify" | Launch Spotify |
| "Open https://..." | Open URL in browser |
| "Search for AI trends" | Google search |
| "Open folder Documents" | Open in file explorer |
| "Create file notes.txt" | Create a new file |
| "Run dir" | Execute terminal command |
| "Take screenshot" | Capture screen |
| "Lock computer" | Lock workstation (requires confirmation) |
| "Minimize all" | Show desktop |

Say **"Hey Mentor"** or **"Jarvis"** as wake words when voice listening is active.

## Configuration

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key (required) |
| `FIRESTORE_PROJECT_ID` | GCP project for Firestore (optional) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Firestore service account JSON |
| `USER_NAME` | Your name for greetings (default: Sir) |
| `ALLOW_SYSTEM_CONTROL` | Enable/disable system commands (default: true) |
| `KNOWLEDGE_DIR` | Path to knowledge folder (default: ../knowledge) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: http://localhost:8000) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (default: ws://localhost:8000) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/greeting` | Proactive greeting |
| POST | `/api/chat` | Send chat message |
| WS | `/api/ws` | Real-time WebSocket |
| POST | `/api/system/command` | Execute system command |
| GET | `/api/memory/history/{id}` | Conversation history |
| GET | `/api/memory/metrics` | Project metrics |
| POST | `/api/rag/refresh` | Re-index knowledge base |

API docs: **http://localhost:8000/docs**

## Multi-Agent System

Queries are routed automatically:

- **Mentor** — General guidance and orchestration
- **CTO** — Architecture, code, DevOps, APIs
- **PM** — Features, roadmaps, sprint planning
- **Marketing** — Branding, launch, growth
- **VC** — Business model, funding, pitch

## Adding Knowledge

Drop Markdown files into `knowledge/` — they are automatically chunked and indexed in ChromaDB on startup. To force re-index:

```bash
curl -X POST http://localhost:8000/api/rag/refresh
```

## Docker

```powershell
# Set your API key
$env:GEMINI_API_KEY = "your-key"
docker-compose up --build
```

## Deploy to Google Cloud Run

```powershell
$env:GEMINI_API_KEY = "your-key"
$env:GCP_PROJECT_ID = "your-project-id"
.\deploy\cloud-run.ps1 -ProjectId $env:GCP_PROJECT_ID
```

> **Note:** System control is disabled by default on Cloud Run (`ALLOW_SYSTEM_CONTROL=false`) since cloud containers cannot control your local machine. Run the backend locally for full system control.

## Security

- Dangerous commands (delete, shutdown, lock) require confirmation
- Set `ALLOW_SYSTEM_CONTROL=false` to disable all system commands
- Never commit `.env` files or credentials
- Use Firestore security rules in production

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, Python 3.11, WebSocket |
| AI | Google Gemini 2.0 Flash |
| Agents | LangGraph multi-agent orchestration |
| RAG | ChromaDB with sentence embeddings |
| Memory | Google Firestore (+ local JSON fallback) |
| Voice | Web Speech API (STT/TTS) |
| System | subprocess, pyautogui, webbrowser |
| Deploy | Google Cloud Run, Docker |

## License

MIT
