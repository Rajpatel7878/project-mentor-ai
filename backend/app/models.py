from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    ROUTER = "router"
    MENTOR = "mentor"
    CTO = "cto"
    PM = "pm"
    MARKETING = "marketing"
    VC = "vc"
    ENGINEER = "engineer"
    OPERATIONS = "operations"
    ANALYST = "analyst"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent: AgentType | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_name: str | None = None
    execute_commands: bool = True


class ChatResponse(BaseModel):
    response: str
    agent: AgentType
    session_id: str
    follow_up_questions: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    command_results: list[dict[str, Any]] = Field(default_factory=list)
    rag_context: list[str] = Field(default_factory=list)


class SystemCommandRequest(BaseModel):
    command: str
    args: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


class SystemCommandResponse(BaseModel):
    success: bool
    message: str
    output: str | None = None
    requires_confirmation: bool = False


class GreetingResponse(BaseModel):
    greeting: str
    time_of_day: str
    user_name: str
    proactive_suggestions: list[str] = Field(default_factory=list)


class UserPreferences(BaseModel):
    name: str = "Sir"
    voice_enabled: bool = True
    wake_words: list[str] = Field(default_factory=lambda: ["hey mentor", "jarvis"])
    project_phase: str = "building"
    theme: str = "holographic"


class WebSocketMessage(BaseModel):
    type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ProjectMetrics(BaseModel):
    total_conversations: int = 0
    decisions_made: int = 0
    tasks_completed: int = 0
    project_phase: str = "building"
    last_active: datetime | None = None


# --- Device & IoT Models ---

class DeviceType(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    SWITCH = "switch"
    SENSOR = "sensor"
    LOCK = "lock"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"


class Device(BaseModel):
    id: str
    name: str
    type: DeviceType
    status: DeviceStatus = DeviceStatus.ONLINE
    protocol: str = "local"  # local, mqtt, homeassistant
    state: dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DeviceActionRequest(BaseModel):
    action: str  # turn_on, turn_off, toggle, set_level, run_diagnostic
    params: dict[str, Any] = Field(default_factory=dict)
    confirm: bool = False


class DeviceActionResponse(BaseModel):
    success: bool
    message: str
    device_id: str
    new_state: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class TelemetrySnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    system: dict[str, Any] = Field(default_factory=dict)
    devices: list[Device] = Field(default_factory=list)


# --- RAG Models ---

class DocumentInfo(BaseModel):
    name: str
    size_bytes: int
    chunk_count: int
    format: str
    uploaded_at: str


class RAGSearchResponse(BaseModel):
    query: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_mode: str = "hybrid"
