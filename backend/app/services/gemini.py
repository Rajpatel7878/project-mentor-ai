"""Google Gemini AI service."""

import json
import logging
import re
from typing import Any

import google.generativeai as genai

logger = logging.getLogger(__name__)

JARVIS_SYSTEM_PROMPT = """You are Project Mentor AI, an intelligent assistant inspired by Tony Stark's JARVIS.
You are a proactive mentor, CTO advisor, product strategist, and personal assistant combined.

Personality:
- Address the user as "sir" or by their name with respect and warmth
- Speak with clarity, confidence, and British eloquence
- Be proactive — suggest next steps, flag risks, ask intelligent follow-up questions
- When executing system commands, confirm what you're doing briefly

Capabilities:
- Deep project knowledge through RAG context
- Architecture, code review, and technical guidance (CTO mode)
- Product strategy and roadmap planning (PM mode)
- Marketing and launch strategy (Marketing mode)
- Business model and funding advice (VC mode)
- System control command parsing

Always structure responses to be helpful and actionable. When appropriate, end with 1-2 follow-up questions.
If project context is provided, ground your answers in it."""

FOLLOW_UP_PROMPT = """Based on this conversation, generate:
1. Two intelligent follow-up questions to guide the user
2. Two proactive suggestions for next steps

Return as JSON: {"follow_up_questions": [...], "suggestions": [...]}"""


from app.agents.registry import agent_registry


class GeminiService:
    """Wrapper for Google Gemini API integrated with swappable AgentRegistry."""

    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.model_name = model_name
        self._model = None
        self.registry = agent_registry
        if api_key:
            genai.configure(api_key=api_key, transport="rest")
            self._model = genai.GenerativeModel(model_name, system_instruction=JARVIS_SYSTEM_PROMPT)
        else:
            logger.warning("Gemini API key not configured.")

    @property
    def AGENT_PROMPTS(self) -> dict[str, str]:
        """Backward compatibility property returning registered agent prompts."""
        return {spec.name: spec.system_prompt for spec in self.registry.list_agents()}

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def _fallback_response(self, message: str, agent: str) -> str:
        return (
            f"Good day, sir. I understand you're asking about: {message[:100]}. "
            f"As your {agent.upper()} advisor, I'd recommend breaking this into smaller actionable steps. "
            f"Please configure your GEMINI_API_KEY to unlock my full intelligence."
        )

    async def generate(self, message: str, context: str = "", history: list[dict[str, str]] | None = None, agent: str = "mentor") -> str:
        if not self._model:
            return self._fallback_response(message, agent)
        prompt_parts = []
        if context:
            prompt_parts.append(f"Project Context (RAG):\n{context}\n")
        if history:
            history_text = "\n".join(f"{h.get('role', 'user').upper()}: {h.get('content', '')}" for h in history[-10:])
            prompt_parts.append(f"Conversation History:\n{history_text}\n")
        
        agent_prompt = self.registry.get_prompt(agent)
        prompt_parts.append(f"Agent Mode: {agent_prompt}")
        prompt_parts.append(f"User: {message}")
        try:
            response = self._model.generate_content("\n".join(prompt_parts))
            return response.text
        except Exception as exc:
            logger.exception("Gemini generation failed: %s", exc)
            err_str = str(exc)
            if "401" in err_str or "invalid authentication" in err_str.lower() or "api_key" in err_str.lower():
                return (
                    "Good day, sir. Your Google Gemini API key appears to be invalid or expired (401 Unauthorized).\n\n"
                    "**To fix this:**\n"
                    "1. Get a free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)\n"
                    "2. Open `backend/.env` and ensure your key begins with `AIzaSy...`:\n"
                    "   ```env\n"
                    "   GEMINI_API_KEY=AIzaSyYourActualKeyHere\n"
                    "   ```\n"
                    "3. Restart the backend server.\n\n"
                    "In the meantime, your **IoT Device Bridge**, **System Telemetry**, and **RAG Knowledge Base** are active and operational."
                )
            return f"I apologize, sir. I encountered an issue: {exc}. Please verify your API key."

    async def generate_follow_ups(self, message: str, response: str, agent: str = "mentor") -> dict[str, list[str]]:
        """Instant zero-latency contextual follow-ups from the active agent specification."""
        return self.registry.get_follow_ups(agent)

    async def route_agent(self, message: str) -> str:
        """Fast instant keyword router delegating to the swappable AgentRegistry."""
        return self.registry.route(message)

    def _keyword_route(self, message: str) -> str:
        """Helper routing method delegating to the swappable AgentRegistry."""
        return self.registry.route(message)

    def get_agent_context(self, agent: str) -> str:
        return self.AGENT_PROMPTS.get(agent, self.AGENT_PROMPTS["mentor"])
