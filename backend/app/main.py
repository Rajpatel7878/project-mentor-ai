"""Project Mentor AI - FastAPI Backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.mentor_graph import MentorAgentSystem
from app.config import get_settings
from app.routers.api import router
from app.services.gemini import GeminiService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.system_control import SystemControlService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

settings = get_settings()
gemini_service: GeminiService | None = None
rag_service: RAGService | None = None
memory_service: MemoryService | None = None
system_control: SystemControlService | None = None
agent_system: MentorAgentSystem | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gemini_service, rag_service, memory_service, system_control, agent_system

    logger.info("Initializing Project Mentor AI services...")

    gemini_service = GeminiService(api_key=settings.gemini_api_key, model_name=settings.gemini_model)
    rag_service = RAGService(knowledge_dir=settings.knowledge_path, persist_dir=settings.chroma_path)
    memory_service = MemoryService(
        project_id=settings.firestore_project_id,
        credentials_path=settings.google_application_credentials,
    )
    system_control = SystemControlService(allow_control=settings.allow_system_control)
    agent_system = MentorAgentSystem(
        gemini=gemini_service,
        rag=rag_service,
        memory=memory_service,
        system_control=system_control,
    )

    logger.info("All services initialized. Mentor AI is online.")
    yield
    logger.info("Shutting down Project Mentor AI...")


app = FastAPI(
    title="Project Mentor AI",
    description="JARVIS-inspired AI mentor with full system control capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "service": "Project Mentor AI",
        "status": "online",
        "docs": "/docs",
        "websocket": "/api/ws",
    }
