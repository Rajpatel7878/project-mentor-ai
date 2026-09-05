"""API route handlers with Device Management and Multi-format RAG support."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect

from app.agents.registry import agent_registry
from app.config import Settings, get_settings
from app.models import (
    ChatRequest,
    ChatResponse,
    Device,
    DeviceActionRequest,
    DeviceActionResponse,
    DocumentInfo,
    GreetingResponse,
    IntakeAnalyzeRequest,
    RAGSearchResponse,
    SystemCommandRequest,
    SystemCommandResponse,
    TelemetrySnapshot,
    UserPreferences,
)
from app.services.analytics import analytics_service
from app.services.greeting import generate_greeting
from app.services.intake import intake_service


logger = logging.getLogger(__name__)

router = APIRouter()


def get_services(settings: Settings = Depends(get_settings)):
    from app.main import agent_system, device_manager, memory_service, rag_service, system_control

    return {
        "agent": agent_system,
        "memory": memory_service,
        "rag": rag_service,
        "system": system_control,
        "devices": device_manager,
        "settings": settings,
    }


@router.get("/health")
async def health_check():
    return {"status": "online", "service": "Project Mentor AI", "version": "2.0.0"}


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


# --- Device & IoT Management Endpoints ---

@router.get("/devices", response_model=list[Device])
async def list_devices(services: dict = Depends(get_services)):
    return services["devices"].list_devices()


@router.get("/devices/telemetry", response_model=TelemetrySnapshot)
async def get_device_telemetry(services: dict = Depends(get_services)):
    return services["devices"].get_telemetry_snapshot()


@router.get("/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, services: dict = Depends(get_services)):
    dev = services["devices"].get_device(device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Device not found")
    return dev


@router.post("/devices/{device_id}/action", response_model=DeviceActionResponse)
async def execute_device_action(
    device_id: str, request: DeviceActionRequest, services: dict = Depends(get_services)
):
    result = services["devices"].execute_action(
        device_id=device_id,
        action=request.action,
        params=request.params,
        confirm=request.confirm,
    )
    return result


# --- Enhanced RAG Endpoints ---

@router.get("/rag/documents", response_model=list[DocumentInfo])
async def list_rag_documents(services: dict = Depends(get_services)):
    return services["rag"].list_documents()


@router.post("/rag/upload", response_model=DocumentInfo)
async def upload_rag_document(file: UploadFile = File(...), services: dict = Depends(get_services)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    allowed_exts = [".md", ".txt", ".json", ".pdf"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400, detail=f"Unsupported format '{ext}'. Allowed: {', '.join(allowed_exts)}"
        )

    content = await file.read()
    doc_info = services["rag"].ingest_file(file.filename, content)
    return DocumentInfo(**doc_info)


@router.delete("/rag/documents/{filename}")
async def delete_rag_document(filename: str, services: dict = Depends(get_services)):
    success = services["rag"].delete_document(filename)
    return {"status": "deleted" if success else "failed", "filename": filename}


@router.post("/rag/refresh")
async def refresh_rag(services: dict = Depends(get_services)):
    count = services["rag"].refresh()
    return {"status": "refreshed", "document_count": count}


@router.get("/rag/search", response_model=RAGSearchResponse)
async def search_knowledge(
    q: str, top_k: int = 5, mode: str = "hybrid", services: dict = Depends(get_services)
):
    results = services["rag"].retrieve(q, top_k=top_k, mode=mode)
    return RAGSearchResponse(query=q, results=results, retrieval_mode=mode)


# --- Memory & Preferences ---

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


# --- Proactive Mentorship ---

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


# --- Swappable Multi-Agent Registry ---

@router.get("/agents")
async def list_registered_agents():
    """List all swappable agent personas registered in the AgentRegistry."""
    return [agent.to_dict() for agent in agent_registry.list_agents()]


# --- Client Intake & Template Recommendation ---

@router.get("/intake/templates")
async def list_intake_templates():
    """List available client solution templates (Customer-Facing, Internal Ops, RAG, Multi-Agent)."""
    return intake_service.list_templates()


@router.post("/intake/analyze")
async def analyze_client_intake(request: IntakeAnalyzeRequest):
    """Analyze client business requirements and return architecture recommendation and ROI projections."""
    return intake_service.analyze(request.model_dump())


# --- Usage & Cost Analytics Dashboard ---

@router.get("/analytics/usage")
async def get_usage_analytics():
    """Get live API call counts, token usage, latency, and estimated cost comparison."""
    return analytics_service.get_summary()


@router.post("/analytics/reset")
async def reset_usage_analytics():
    """Reset usage counters for a fresh client demonstration."""
    analytics_service.reset_metrics()
    return {"status": "reset", "message": "Usage and cost metrics reset successfully."}



# --- Real-Time WebSockets with Telemetry Broadcasting ---

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
        for connection in list(self.active):
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    from app.main import agent_system, device_manager, memory_service

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

            elif msg_type == "device_action":
                dev_id = data.get("device_id")
                action = data.get("action")
                params = data.get("params", {})
                confirm = data.get("confirm", False)
                res = device_manager.execute_action(dev_id, action, params, confirm)
                await websocket.send_json({"type": "device_action_result", "payload": res.model_dump()})

                # Broadcast updated telemetry to active sockets
                snap = device_manager.get_telemetry_snapshot()
                await manager.broadcast({"type": "telemetry", "payload": snap.model_dump()})

            elif msg_type == "get_telemetry":
                snap = device_manager.get_telemetry_snapshot()
                await websocket.send_json({"type": "telemetry", "payload": snap.model_dump()})

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
