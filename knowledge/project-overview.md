# Project Mentor AI - Knowledge Base

## Project Overview

Project Mentor AI is a JARVIS-inspired intelligent assistant that combines:
- Proactive mentoring across technical, product, marketing, and business domains
- Full system control capabilities (open apps, run commands, browse web)
- Long-term memory via Firestore
- RAG-powered project context from this knowledge base

## Architecture

### Frontend
- Next.js 14 with TypeScript
- Tailwind CSS + Framer Motion for holographic UI
- Web Speech API for voice I/O
- WebSocket for real-time communication

### Backend
- FastAPI with Python 3.11+
- Google Gemini 2.0 Flash for AI
- ChromaDB for local RAG
- LangGraph multi-agent orchestration
- Firestore for persistent memory

### Agents
1. **Router Agent** - Routes queries to specialists
2. **Mentor Agent** - Orchestrates overall guidance
3. **CTO Agent** - Architecture, code, DevOps
4. **PM Agent** - Product strategy, roadmaps
5. **Marketing Agent** - Go-to-market, branding
6. **VC Agent** - Business model, funding

## Current Phase: Building

We are in the active development phase. Key priorities:
- Core chat and voice interaction
- System control command parsing
- RAG knowledge retrieval
- Multi-agent routing

## Technical Decisions

- **AI Model**: Gemini 2.0 Flash for speed and cost efficiency
- **Vector DB**: ChromaDB for local, persistent embeddings
- **Memory**: Firestore with local JSON fallback for offline dev
- **Deployment**: Google Cloud Run for both frontend and backend

## Voice Commands

Supported system control commands:
- "Open Chrome/VS Code/Terminal/Spotify"
- "Open [URL]" - Opens in default browser
- "Search for [query]" - Google search
- "Open folder [path]" - File explorer
- "Create file [name]" - Create new file
- "Delete [file]" - Delete with confirmation
- "Run [command]" - Execute terminal command
- "Take screenshot" - Capture screen
- "Lock computer" - Lock workstation
- "Minimize all" / "Show desktop"

## Security Notes

- Dangerous commands require explicit confirmation
- System control can be disabled via ALLOW_SYSTEM_CONTROL=false
- API keys stored in environment variables only
