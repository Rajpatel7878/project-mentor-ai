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


class GeminiService:
    """Wrapper for Google Gemini API."""

    AGENT_PROMPTS = {
        "mentor": "You are the Mentor Agent — orchestrate guidance across all domains with wisdom and clarity.",
        "cto": "You are the CTO Agent — expert in software architecture, code quality, DevOps, and technical decisions.",
        "pm": "You are the PM Agent — expert in product strategy, roadmaps, sprint planning, and user needs.",
        "marketing": "You are the Marketing Agent — expert in go-to-market strategy, branding, and user acquisition.",
        "vc": "You are the VC Agent — expert in business models, fundraising, market sizing, and investor relations.",
    }

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._model = None
        if api_key:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(model_name, system_instruction=JARVIS_SYSTEM_PROMPT)
        else:
            logger.warning("Gemini API key not configured.")

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
        prompt_parts.append(f"Agent Mode: {self.AGENT_PROMPTS.get(agent, self.AGENT_PROMPTS['mentor'])}")
        prompt_parts.append(f"User: {message}")
        try:
            response = self._model.generate_content("\n".join(prompt_parts))
            return response.text
        except Exception as exc:
            logger.exception("Gemini generation failed")
            return f"I apologize, sir. I encountered an issue: {exc}. Please verify your API key."

    async def generate_follow_ups(self, message: str, response: str) -> dict[str, list[str]]:
        if not self._model:
            return {
                "follow_up_questions": ["Would you like me to break this down into actionable tasks?", "Should we consider the scalability implications?"],
                "suggestions": ["Document this decision in your project knowledge base.", "Schedule a review session to validate this approach."],
            }
        try:
            result = self._model.generate_content(f"{FOLLOW_UP_PROMPT}\n\nUser: {message}\nAssistant: {response}")
            json_match = re.search(r"\{.*\}", result.text.strip(), re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as exc:
            logger.warning("Follow-up generation failed: %s", exc)
        return {"follow_up_questions": ["What aspect would you like to explore further, sir?"], "suggestions": ["Consider updating your project documentation with today's decisions."]}

    async def route_agent(self, message: str) -> str:
        if not self._model:
            return self._keyword_route(message)
        try:
            result = self._model.generate_content(f"Classify into ONE agent: mentor, cto, pm, marketing, vc\n\nMessage: {message}\n\nRespond with ONLY the agent name.")
            agent = result.text.strip().lower()
            return agent if agent in self.AGENT_PROMPTS else "mentor"
        except Exception:
            return self._keyword_route(message)

    def _keyword_route(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["code", "architecture", "api", "database", "deploy", "bug", "test"]):
            return "cto"
        if any(w in msg for w in ["feature", "roadmap", "sprint", "task", "priority", "user story"]):
            return "pm"
        if any(w in msg for w in ["marketing", "brand", "launch", "social", "campaign", "seo"]):
            return "marketing"
        if any(w in msg for w in ["funding", "investor", "revenue", "business model", "pitch", "vc"]):
            return "vc"
        return "mentor"

    def get_agent_context(self, agent: str) -> str:
        return self.AGENT_PROMPTS.get(agent, self.AGENT_PROMPTS["mentor"])
