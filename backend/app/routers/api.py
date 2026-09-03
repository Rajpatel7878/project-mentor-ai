"""API route handlers."""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.config import Settings, get_settings
from app.models import (
    ChatRequest,
    ChatResponse,
    GreetingResponse,
    SystemCommandRequest,
    SystemCommandResponse,
    UserPreferences,
)
from app.services.greeting import generate_greeting

logger = logging.getLogger(__name__)

router = APIRouter()


def get_services(settings: Settings = Depends(get_settings)):
    from app.main import agent_system, memory_service, rag_service, system_control

    return {
        "agent": agent_system,
        "memory": memory_service,
        "rag": rag_service,
        "system": system_control,
        "settings": settings,
    }


@router.get("/health")
async def health_check():
    return {"status": "online", "service": "Project Mentor AI", "version": "1.0.0"}


@router.get("/greeting", response_model=GreetingResponse)
async def get_greeting(services: dict = Depends(get_services)):
    prefs = await services["memory"].get_preferences()
    result = generate_greeting(prefs.get("name", "Sir"), prefs.get("project_phase", "building"))
    return GreetingResponse(**result)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, services: dict = Depends(get_services)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    prefs = await services["memory"].get_preferences()
    user_name = request.user_name or prefs.get("name", "Sir")

    result = await services["agent"].process(
        message=request.message,
        session_id=request.session_id,
        user_name=user_name,
        execute_commands=request.execute_commands,
    )

    return ChatResponse(**result)


@router.post("/system/command", response_model=SystemCommandResponse)
async def execute_system_command(request: SystemCommandRequest, services: dict = Depends(get_services)):
    system = services["system"]
    result: dict[str, Any]

    if request.command in system.__class__.__dict__ or hasattr(system, request.command):
        method = getattr(system, request.command, None)
        if callable(method):
            result = method(**request.args, confirm=request.confirm)
        else:
            result = system.execute_named_command(request.command, confirm=request.confirm, **request.args)
    else:
        result = system.execute_named_command(request.command, confirm=request.confirm, **request.args)

    return SystemCommandResponse(
        success=result.get("success", False),
        message=result.get("message", ""),
        output=result.get("output"),
        requires_confirmation=result.get("requires_confirmation", False),
    )


@router.get("/memory/history/{session_id}")
async def get_history(session_id: str, limit: int = 20, services: dict = Depends(get_services)):
    history = await services["memory"].get_conversation_history(session_id, limit)
    return {"session_id": session_id, "messages": history}


@router.get("/memory/preferences", response_model=UserPreferences)
async def get_preferences(services: dict = Depends(get_services)):
    prefs = await services["memory"].get_preferences()
    return UserPreferences(**prefs)


@router.put("/memory/preferences")
async def update_preferences(preferences: UserPreferences, services: dict = Depends(get_services)):
    await services["memory"].save_preferences("default", preferences.model_dump())
    return {"status": "updated", "preferences": preferences}


@router.get("/memory/metrics")
async def get_metrics(services: dict = Depends(get_services)):
    metrics = await services["memory"].get_metrics()
    decisions = await services["memory"].get_recent_decisions(5)
    return {"metrics": metrics, "recent_decisions": decisions}


@router.post("/rag/refresh")
async def refresh_rag(services: dict = Depends(get_services)):
    count = services["rag"].refresh()
    return {"status": "refreshed", "document_count": count}


@router.get("/rag/search")
async def search_knowledge(q: str, top_k: int = 5, services: dict = Depends(get_services)):
    results = services["rag"].retrieve(q, top_k)
    return {"query": q, "results": results}


@router.get("/proactive/standup")
async def get_standup(session_id: str = "default", services: dict = Depends(get_services)):
    from app.main import gemini_service, memory_service
    from app.services.proactive import ProactiveService

    proactive = ProactiveService(gemini_service, memory_service)
    summary = await proactive.generate_standup(session_id)
    return {"standup": summary, "generated_at": datetime.utcnow().isoformat()}


@router.post("/proactive/sprint-plan")
async def create_sprint_plan(goals: str, services: dict = Depends(get_services)):
    from app.main import gemini_service, memory_service
    from app.services.proactive import ProactiveService

    proactive = ProactiveService(gemini_service, memory_service)
    plan = await proactive.generate_sprint_plan(goals)
    return {"plan": plan}


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    from app.main import agent_system, memory_service

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "chat")

            if msg_type == "chat":
                message = data.get("message", "")
                session_id = data.get("session_id", "default")
                prefs = await memory_service.get_preferences()
                user_name = data.get("user_name") or prefs.get("name", "Sir")

                await websocket.send_json({"type": "thinking", "payload": {"status": "processing"}})

                result = await agent_system.process(
                    message=message,
                    session_id=session_id,
                    user_name=user_name,
                    execute_commands=data.get("execute_commands", True),
                )

                await websocket.send_json({"type": "response", "payload": result})

            elif msg_type == "greeting":
                prefs = await memory_service.get_preferences()
                greeting = generate_greeting(prefs.get("name", "Sir"), prefs.get("project_phase", "building"))
                await websocket.send_json({"type": "greeting", "payload": greeting})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong", "payload": {}})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.exception("WebSocket error")
        manager.disconnect(websocket)
        try:
            await websocket.send_json({"type": "error", "payload": {"message": str(exc)}})
        except Exception:
            pass
