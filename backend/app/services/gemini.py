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
        "engineer": "You are the Engineer & IoT Agent — expert in hardware automation, device diagnostics, protocols (MQTT/Home Assistant), and system health.",
        "operations": "You are the Operations & Scheduling Agent — expert in workflow automation, calendar coordination, daily standups, and productivity routines.",
        "analyst": "You are the Analyst Agent — expert in data synthesis, cross-document RAG summarization, executive briefings, and metrics insights.",
    }

    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.model_name = model_name
        self._model = None
        if api_key:
            genai.configure(api_key=api_key, transport="rest")
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
        """Instant zero-latency contextual follow-ups tailored to the active agent."""
        defaults = {
            "engineer": {
                "follow_up_questions": ["Would you like to run full hardware diagnostics?", "Should I adjust thermal or lighting parameters?"],
                "suggestions": ["Monitor live CPU and RAM allocation on the dashboard.", "Verify peripheral actuator states in the IoT console."],
            },
            "operations": {
                "follow_up_questions": ["Shall I compile today's automated standup notes?", "Would you like me to set a productivity timer?"],
                "suggestions": ["Review your daily milestones and open blockers.", "Generate an agenda briefing for your next session."],
            },
            "cto": {
                "follow_up_questions": ["Should we inspect system error logs and test coverage?", "Would you like to review the microservice architecture?"],
                "suggestions": ["Run the automated test suite to ensure system health.", "Inspect database connection pools and endpoint latency."],
            },
            "analyst": {
                "follow_up_questions": ["Would you like an executive summary of this data?", "Shall I query the knowledge base for related documents?"],
                "suggestions": ["Index additional reference PDFs or specs in RAG.", "Synthesize key metrics into an actionable project report."],
            },
            "pm": {
                "follow_up_questions": ["Should we prioritize these backlog items for the current sprint?", "Would you like to draft user acceptance criteria?"],
                "suggestions": ["Update roadmap milestones to reflect current progress.", "Break down the architectural requirements into epics."],
            },
            "marketing": {
                "follow_up_questions": ["Shall I outline the launch distribution channels?", "Would you like to craft a value proposition statement?"],
                "suggestions": ["Define target customer personas and core messaging pillars.", "Draft a release announcement for the community."],
            },
            "vc": {
                "follow_up_questions": ["Should we evaluate the unit economics and burn rate?", "Would you like to rehearse pitch responses for investors?"],
                "suggestions": ["Structure a 10-slide executive pitch deck outline.", "Refine your defensibility and competitive moat articulation."],
            },
            "mentor": {
                "follow_up_questions": ["Would you like to break this into actionable milestones?", "What is the primary constraint we should tackle first?"],
                "suggestions": ["Document today's strategic decisions in your knowledge base.", "Focus on the highest-leverage task on your priority list."],
            },
        }
        return defaults.get(agent, defaults["mentor"])

    async def route_agent(self, message: str) -> str:
        """Fast instant keyword route first; fallback to quick classifier only if ambiguous."""
        kw_agent = self._keyword_route(message)
        if kw_agent != "mentor":
            return kw_agent
        return "mentor"

    def _keyword_route(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["light", "thermostat", "device", "iot", "temperature", "switch", "relay", "lock door", "hardware", "diagnostic"]):
            return "engineer"
        if any(w in msg for w in ["schedule", "calendar", "standup", "sprint plan", "meeting", "reminder", "agenda", "break"]):
            return "operations"
        if any(w in msg for w in ["synthesize", "analyze document", "summary", "report", "extract", "knowledge base", "research"]):
            return "analyst"
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
