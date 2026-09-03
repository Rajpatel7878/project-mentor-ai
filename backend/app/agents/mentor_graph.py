"""LangGraph multi-agent orchestration system with IoT Device Bridge and RAG integration."""

import logging
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.device_bridge import DeviceManager
from app.services.gemini import GeminiService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.system_control import SystemControlService

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    message: str
    session_id: str
    user_name: str
    agent: str
    rag_context: str
    device_context: str
    history: list[dict[str, str]]
    response: str
    follow_up_questions: list[str]
    suggestions: list[str]
    command_results: list[dict[str, Any]]
    execute_commands: bool


class MentorAgentSystem:
    """Multi-agent system orchestrating 8 specialized domain agents with IoT & RAG tools."""

    def __init__(
        self,
        gemini: GeminiService,
        rag: RAGService,
        memory: MemoryService,
        system_control: SystemControlService,
        device_manager: DeviceManager,
    ):
        self.gemini = gemini
        self.rag = rag
        self.memory = memory
        self.system_control = system_control
        self.device_manager = device_manager
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("route", self._route)
        workflow.add_node("dispatch_commands", self._execute_commands)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("generate_follow_ups", self._generate_follow_ups)

        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "route")
        workflow.add_edge("route", "dispatch_commands")
        workflow.add_edge("dispatch_commands", "generate_response")
        workflow.add_edge("generate_response", "generate_follow_ups")
        workflow.add_edge("generate_follow_ups", END)

        return workflow.compile()

    async def _retrieve_context(self, state: AgentState) -> dict[str, Any]:
        # Hybrid RAG Context
        context = self.rag.get_context_string(state["message"])
        history = await self.memory.get_conversation_history(state["session_id"])
        history_formatted = [{"role": h.get("role", "user"), "content": h.get("content", "")} for h in history]

        # Device Snapshot Context
        snap = self.device_manager.get_telemetry_snapshot()
        dev_summaries = [
            f"{d.name} ({d.type.value}): Status={d.status.value}, State={d.state}"
            for d in snap.devices
        ]
        dev_context = f"Host CPU: {snap.system.get('cpu_percent', 0)}%, RAM: {snap.system.get('ram_percent', 0)}%\n" + "\n".join(dev_summaries)

        return {"rag_context": context, "device_context": dev_context, "history": history_formatted}

    async def _route(self, state: AgentState) -> dict[str, Any]:
        agent = await self.gemini.route_agent(state["message"])
        return {"agent": agent}

    async def _execute_commands(self, state: AgentState) -> dict[str, Any]:
        if not state.get("execute_commands", True):
            return {"command_results": []}

        all_results: list[dict[str, Any]] = []

        # 1. Check & execute device automation commands
        device_results = self.device_manager.parse_and_execute_device_command(state["message"])
        all_results.extend(device_results)

        # 2. Check & execute local OS commands
        sys_results = self.system_control.parse_and_execute(state["message"])
        all_results.extend(sys_results)

        return {"command_results": all_results}

    async def _generate_response(self, state: AgentState) -> dict[str, Any]:
        context_parts = []

        # Grounding with RAG
        if state.get("rag_context"):
            context_parts.append(f"Knowledge Base (RAG):\n{state['rag_context']}")

        # Grounding with Device Telemetry for Engineer or System queries
        if state.get("agent") in ["engineer", "mentor", "cto"] or "device" in state["message"].lower():
            if state.get("device_context"):
                context_parts.append(f"Real-Time Device & Hardware Telemetry:\n{state['device_context']}")

        # Executed command feedback
        if state.get("command_results"):
            cmd_summary = "\n".join(
                f"- {r.get('message', 'Executed action')}: {'Success' if r.get('success') else 'Failed'}"
                for r in state["command_results"]
            )
            context_parts.append(f"System & Device Actions Executed:\n{cmd_summary}")

        response = await self.gemini.generate(
            message=state["message"],
            context="\n\n".join(p for p in context_parts if p),
            history=state.get("history", []),
            agent=state.get("agent", "mentor"),
        )
        return {"response": response}

    async def _generate_follow_ups(self, state: AgentState) -> dict[str, Any]:
        follow_ups = await self.gemini.generate_follow_ups(state["message"], state["response"])
        return {
            "follow_up_questions": follow_ups.get("follow_up_questions", []),
            "suggestions": follow_ups.get("suggestions", []),
        }

    async def process(
        self,
        message: str,
        session_id: str = "default",
        user_name: str = "Sir",
        execute_commands: bool = True,
    ) -> dict[str, Any]:
        initial_state: AgentState = {
            "message": message,
            "session_id": session_id,
            "user_name": user_name,
            "agent": "mentor",
            "rag_context": "",
            "device_context": "",
            "history": [],
            "response": "",
            "follow_up_questions": [],
            "suggestions": [],
            "command_results": [],
            "execute_commands": execute_commands,
        }

        result = await self.graph.ainvoke(initial_state)

        await self.memory.save_message(session_id, "user", message)
        await self.memory.save_message(session_id, "assistant", result["response"], agent=result.get("agent"))

        metrics = await self.memory.get_metrics()
        await self.memory.update_metrics({"total_conversations": metrics.get("total_conversations", 0) + 1})

        # Retrieve top RAG context preview
        rag_preview = [c["text"][:200] for c in self.rag.retrieve(message, top_k=3)]

        return {
            "response": result["response"],
            "agent": result.get("agent", "mentor"),
            "session_id": session_id,
            "follow_up_questions": result.get("follow_up_questions", []),
            "suggestions": result.get("suggestions", []),
            "command_results": result.get("command_results", []),
            "rag_context": rag_preview,
        }
