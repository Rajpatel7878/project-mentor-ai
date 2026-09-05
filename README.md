# Project Mentor AI (Jarvis 2.0)

A client-ready, JARVIS-inspired autonomous ecosystem featuring swappable multi-agent personas, local IoT device automation, enterprise hybrid RAG, client intake recommendation, and real-time usage/cost telemetry.

![Stack](https://img.shields.io/badge/Next.js-14-black) ![Stack](https://img.shields.io/badge/FastAPI-Python-blue) ![Stack](https://img.shields.io/badge/Gemini-2.0_Flash-orange) ![Stack](https://img.shields.io/badge/ChromaDB-Local_RAG-green) ![Stack](https://img.shields.io/badge/Cost_Savings-97%25-brightgreen)

---

## What's New in v2.0 Client Suite

- **Swappable Multi-Agent Registry (`AgentRegistry`)** — Dynamic domain personas (Mentor, CTO, PM, Marketing, VC, Engineer, Operations, Analyst) routed by weighted keyword relevance. New personas can be registered at runtime without modifying core code.
- **Client Intake & Architecture Recommender** — 1-click interactive intake wizard that analyzes business bottlenecks, evaluates constraints, and generates an architectural recommendation with monthly token budgets and 5-phase implementation roadmaps.
- **Real-Time Usage & Cost Accounting** — Sub-penny precision telemetry tracking token counts, latency (ms), and actual cost per agent. Highlights over **96.5% - 98% operational savings** versus proprietary enterprise models (GPT-4o benchmark).
- **Self-Healing Deployment** — Automatic `.env` bootstrapping from `.env.example` templates in `start.bat` and trimmed `.dockerignore` files reducing Docker build contexts from 3.2 GB to under 45 MB.
- **Zero-Cost Enterprise Foundation** — Self-hosted local ChromaDB vector store (no Pinecone fees) and resilient local JSON memory fallback (no mandatory Firestore cloud bill).

---

## Features

- **Proactive Greeting** — Time-aware welcome with conversational audio feedback.
- **Voice Control** — Web Speech API with "Hey Mentor" and "Jarvis" wake word support.
- **System & IoT Bridge** — Local host automation (terminal, apps, screenshots) and IoT smart device control (lighting, thermostats, security locks) with Human-In-The-Loop (HITL) safety verification.
- **LangGraph StateGraph** — Stateful multi-agent execution pipeline integrating hybrid RAG and hardware telemetry snapshots.
- **Hybrid RAG Pipeline** — ChromaDB indexing across `.md`, `.txt`, `.json`, and `.pdf` files with dense semantic + BM25 keyword retrieval.
- **Holographic Glassmorphism UI** — Real-time particle background, audio sound effects, Framer Motion transitions, and interactive views.

---

## Project Structure

```
project-mentor-ai/
├── backend/                       # FastAPI Python backend
│   ├── app/
│   │   ├── agents/                # LangGraph workflow & swappable AgentRegistry
│   │   │   ├── mentor_graph.py    # LangGraph StateGraph pipeline
│   │   │   └── registry.py        # Swappable AgentRegistry & AgentSpec personas
│   │   ├── routers/               # API endpoints & WebSocket handler
│   │   │   └── api.py             # Chat, RAG, Devices, Agents, Intake, Analytics
│   │   ├── services/              # Core domain services
│   │   │   ├── analytics.py       # Live token, latency & cost tracking service
│   │   │   ├── device_bridge.py   # IoT device abstraction layer & host telemetry
│   │   │   ├── gemini.py          # Google Gemini Flash client
│   │   │   ├── greeting.py        # Contextual greeting generator
│   │   │   ├── intake.py          # Client intake & ROI recommendation engine
│   │   │   ├── memory.py          # Memory service (Firestore + Local fallback)
│   │   │   ├── proactive.py       # Automated standup & sprint planning service
│   │   │   ├── rag.py             # Multi-format ChromaDB RAG service
│   │   │   └── system_control.py  # Local OS execution & HITL security guards
│   │   ├── config.py              # Pydantic BaseSettings
│   │   ├── models.py              # Pydantic models & API schemas
│   │   └── main.py                # FastAPI application entrypoint
│   ├── test_jarvis.py             # 6-part automated verification test suite
│   ├── requirements.txt
│   ├── .dockerignore
│   └── Dockerfile
├── frontend/                      # Next.js 14 frontend (App Router)
│   ├── src/
│   │   ├── app/                   # Next.js pages & layout
│   │   ├── components/            # UI components
│   │   │   ├── AnalyticsDashboard.tsx   # Live cost & token telemetry view
│   │   │   ├── ClientIntakeWizard.tsx   # Interactive intake & ROI wizard
│   │   │   ├── DeviceDashboard.tsx      # IoT devices & host hardware status
│   │   │   ├── KnowledgeManager.tsx     # Drag-and-drop RAG document manager
│   │   │   ├── MentorDashboard.tsx      # Main holographic dashboard container
│   │   │   └── ...                      # ChatInterface, VoiceControl, etc.
│   │   ├── hooks/                 # WebSocket & Voice hooks
│   │   └── lib/                   # API client & sound effects
│   ├── .dockerignore
│   └── Dockerfile
├── knowledge/                     # RAG knowledge base (Markdown & documents)
├── CHANGELOG.md                   # Detailed change log & engineering case study
├── CLIENT_DEMO_CHECKLIST.md       # 5-minute client demonstration playbook
├── docker-compose.yml             # Container orchestration
├── start.bat                      # Self-healing 1-click Windows launcher
└── .env.example                   # Full environment variable reference
```

---

## Quick Start

### 1-Click Launch (Windows)

Simply double-click `start.bat` (or run it in PowerShell/Command Prompt):
```powershell
.\start.bat
```
`start.bat` automatically:
1. Detects and copies `.env.example` to `.env` (root and backend) if missing.
2. Initializes `frontend/.env.local` from its example template.
3. Activates the Python virtual environment and launches FastAPI on `http://localhost:8000`.
4. Starts Next.js 14 on `http://localhost:3000`.

### Docker Compose

```powershell
# Copy environment configuration
copy .env.example .env

# Build and start all services
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- FastAPI Docs: `http://localhost:8000/docs`

---

## Swappable Agent Council

Queries are automatically classified and routed via score-based relevance in `AgentRegistry`:

| Persona | Domain Expertise | Example Trigger Keywords |
|---------|------------------|--------------------------|
| **Mentor** | Executive advisor & overall coordinator | *mentor, advice, goal, priority, strategy* |
| **CTO** | Distributed systems, APIs, code architecture | *architecture, database, postgres, api, refactor* |
| **PM** | User stories, backlog grooming, sprint velocity | *sprint, user story, roadmap, feature, deadline* |
| **Marketing** | Product positioning, launch copy, campaigns | *marketing, launch, branding, copy, seo, campaign* |
| **VC** | Pitch decks, cap tables, fundraising metrics | *investor, funding, seed, valuation, pitch deck, arr* |
| **Engineer** | IoT hardware, smart home, host system commands | *device, light, thermostat, temperature, command, lock* |
| **Operations** | Daily standup synthesis, blocker triage | *standup, blocker, workflow, automation, daily sync* |
| **Analyst** | Deep document research & RAG synthesis | *research, report, analyze, synthesis, document, rag* |

---

## API Endpoints Reference

### Core & Assistants
- `GET /api/health` — System health and version.
- `GET /api/greeting` — Context-aware time-of-day greeting.
- `POST /api/chat` — Send query to multi-agent LangGraph workflow.
- `WS /api/ws` — High-speed real-time WebSocket connection.
- `GET /api/agents` — List all registered personas in `AgentRegistry`.

### Client Intake & Solutions
- `GET /api/intake/templates` — List available solution blueprints.
- `POST /api/intake/analyze` — Analyze client bottlenecks and return ROI projections.

### Usage & Cost Analytics
- `GET /api/analytics/usage` — Live token counts, latency, and cost comparison.
- `POST /api/analytics/reset` — Reset counters for clean demonstrations.

### IoT & System Control
- `GET /api/devices` — List registered smart devices and states.
- `GET /api/devices/telemetry` — Host hardware stats (CPU, RAM) + device snapshot.
- `POST /api/devices/{id}/action` — Trigger device state mutation.
- `POST /api/system/command` — Run local host command (with HITL security guard).

### Knowledge & RAG
- `GET /api/rag/documents` — List indexed documents.
- `POST /api/rag/upload` — Ingest `.md`, `.txt`, `.json`, or `.pdf` file.
- `DELETE /api/rag/documents/{filename}` — Remove document and purge vectors.
- `GET /api/rag/search?q={query}` — Perform hybrid semantic + keyword search.

---

## Automated Verification Suite

Run the full automated test suite covering all 6 system layers:
```powershell
backend\venv\Scripts\python.exe backend/test_jarvis.py
```
**Test Coverage:**
1. Device Bridge & Hardware Abstraction Layer
2. Enhanced Hybrid RAG Pipeline (ChromaDB)
3. Multi-Agent Routing & LangGraph Execution
4. Swappable Agent Registry & Custom Personas
5. Client Intake & Template Recommendation
6. Usage, Cost & ROI Analytics

---

## Client Demonstration

Refer to [CLIENT_DEMO_CHECKLIST.md](file:///d:/project%20mentor%20ai/CLIENT_DEMO_CHECKLIST.md) for a step-by-step 5-minute presentation script designed to win client engagements.

For detailed architecture notes and historical upgrade rationale, see [CHANGELOG.md](file:///d:/project%20mentor%20ai/CHANGELOG.md).

---

## License

MIT License. Designed and engineered for high-performance agentic workflows.
