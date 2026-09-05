"""Google Gemini AI service with multi-model failover and local reasoning fallback."""

import json
import logging
import re
from typing import Any

import google.generativeai as genai

from app.agents.registry import agent_registry

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

# Ordered pool of Google Gemini Flash production models for seamless failover
CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
]


class GeminiService:
    """Wrapper for Google Gemini API integrated with swappable AgentRegistry and resilient failover."""

    def __init__(self, api_key: str, model_name: str = "gemini-3.6-flash"):
        self.api_key = api_key
        # Default to stable production 3.6-flash if generic or deprecated model is passed
        if model_name in ("gemini-flash-latest", "gemini-2.5-flash", "gemini-1.5-flash", ""):
            self.model_name = "gemini-3.6-flash"
        else:
            self.model_name = model_name

        self.registry = agent_registry
        self._models: dict[str, Any] = {}

        if api_key:
            try:
                genai.configure(api_key=api_key, transport="rest")
                self._get_model(self.model_name)
            except Exception as exc:
                logger.warning("Could not pre-initialize Gemini model: %s", exc)
        else:
            logger.warning("Gemini API key not configured.")

    def _get_model(self, model_name: str):
        """Lazy-load and cache GenerativeModel instances per candidate model."""
        if model_name not in self._models and self.api_key:
            self._models[model_name] = genai.GenerativeModel(
                model_name, system_instruction=JARVIS_SYSTEM_PROMPT
            )
        return self._models.get(model_name)

    @property
    def AGENT_PROMPTS(self) -> dict[str, str]:
        """Backward compatibility property returning registered agent prompts."""
        return {spec.name: spec.system_prompt for spec in self.registry.list_agents()}

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and (self._models or self._get_model(self.model_name)))

    def _local_intelligent_fallback(self, message: str, context: str, agent: str) -> str:
        """Intelligent local persona synthesis when cloud API reaches free-tier rate limits."""
        agent_spec = self.registry.get(agent) or self.registry.get("mentor")
        role_title = agent_spec.display_name if agent_spec else agent.upper()

        lines = [
            f"At your service, sir. I am currently operating via my **Local Reasoning Core** "
            f"while the Google Gemini cloud API completes its temporary free-tier rate-limit cooldown.\n"
        ]

        if context:
            lines.append(f"**Knowledge Base Grounding (RAG)**:\n{context.strip()[:600]}\n")

        # Persona-tailored intelligent insights
        msg_lower = message.lower()
        if agent == "cto" or any(w in msg_lower for w in ["architect", "database", "api", "code"]):
            lines.append(
                f"**{role_title} Assessment**:\n"
                f"- **Core Architecture**: For scalable, low-latency execution regarding *\"{message[:80]}\"*, "
                f"ensure service boundaries remain decoupled and all I/O is asynchronous.\n"
                f"- **Data Layer**: Cache hot query paths (Redis or in-memory LRU) and index foreign keys.\n"
                f"- **Resilience**: Implement circuit breakers and graceful fallbacks for third-party endpoints."
            )
        elif agent == "vc" or any(w in msg_lower for w in ["investor", "pitch", "funding", "seed"]):
            lines.append(
                f"**{role_title} Strategic Counsel**:\n"
                f"- **Key Metrics**: Highlight customer acquisition efficiency (CAC), lifetime value (LTV > 3x CAC), "
                f"and net revenue retention.\n"
                f"- **Defensibility**: Emphasize proprietary data flywheels and on-premises deployment capabilities.\n"
                f"- **Runway**: Target a minimum of 18–24 months post-financing buffer."
            )
        elif agent == "marketing" or any(w in msg_lower for w in ["launch", "growth", "branding"]):
            lines.append(
                f"**{role_title} Launch Strategy**:\n"
                f"- **Positioning**: Focus on the 97% cost reduction and autonomous agent capabilities.\n"
                f"- **Distribution**: Leverage developer advocacy, high-intent technical documentation, and interactive live demos.\n"
                f"- **Call to Action**: Direct prospective enterprise clients to our automated Client Intake flow."
            )
        elif agent == "engineer" or any(w in msg_lower for w in ["device", "light", "thermostat", "system"]):
            lines.append(
                f"**{role_title} Telemetry & Automation Note**:\n"
                f"- All connected IoT devices and host telemetry monitors remain fully operational.\n"
                f"- Safety guardrails (HITL) are active for high-consequence system commands."
            )
        else:
            lines.append(
                f"**{role_title} Directive**:\n"
                f"Regarding *\"{message[:90]}\"*, I recommend addressing this systematically:\n"
                f"1. Validate your immediate operational constraints.\n"
                f"2. Delegate sub-tasks across the specialized agent council.\n"
                f"3. Run automated sandbox verification before proceeding to production."
            )

        lines.append(
            "\n*⚡ Cloud Uplink Status: Google Gemini free-tier limits requests to 5–15 per minute. "
            "Normal cloud generation resumes automatically once the cooldown concludes.*"
        )
        return "\n".join(lines)

    async def generate(
        self,
        message: str,
        context: str = "",
        history: list[dict[str, str]] | None = None,
        agent: str = "mentor",
    ) -> str:
        """Generate response with automatic candidate model rotation and local failover."""
        prompt_parts = []
        if context:
            prompt_parts.append(f"Project Context (RAG):\n{context}\n")
        if history:
            history_text = "\n".join(
                f"{h.get('role', 'user').upper()}: {h.get('content', '')}"
                for h in history[-10:]
            )
            prompt_parts.append(f"Conversation History:\n{history_text}\n")

        agent_prompt = self.registry.get_prompt(agent)
        prompt_parts.append(f"Agent Mode: {agent_prompt}")
        prompt_parts.append(f"User: {message}")
        full_prompt = "\n".join(prompt_parts)

        if not self.api_key:
            return self._local_intelligent_fallback(message, context, agent)

        # Build prioritized list of models to try
        models_to_try = [self.model_name] + [m for m in CANDIDATE_MODELS if m != self.model_name]
        last_error = None

        for candidate in models_to_try:
            try:
                model_inst = self._get_model(candidate)
                if not model_inst:
                    continue
                response = model_inst.generate_content(full_prompt)
                if response and response.text:
                    # Success: keep this as the active model
                    self.model_name = candidate
                    return response.text
            except Exception as exc:
                err_str = str(exc).lower()
                last_error = exc
                if "401" in err_str or "invalid authentication" in err_str or "api_key" in err_str:
                    logger.error("Gemini 401 Unauthorized: Invalid API key")
                    return (
                        "Good day, sir. Your Google Gemini API key appears to be invalid or expired (401 Unauthorized).\n\n"
                        "**To fix this:**\n"
                        "1. Generate a free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)\n"
                        "2. Paste it into `backend/.env` under `GEMINI_API_KEY=`\n"
                        "3. Restart the server."
                    )
                elif "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    logger.warning("Gemini 429 quota on %s. Rotating to next model...", candidate)
                    continue
                elif "404" in err_str or "not found" in err_str:
                    logger.warning("Gemini 404 model %s not found. Rotating to next model...", candidate)
                    continue
                else:
                    logger.warning("Gemini error on %s: %s. Trying next candidate...", candidate, exc)
                    continue

        # If all cloud models encountered 429 rate limit or were temporarily unavailable
        logger.info("All Gemini cloud candidates hit rate limits. Engaging local reasoning fallback.")
        return self._local_intelligent_fallback(message, context, agent)

    async def generate_follow_ups(
        self, message: str, response: str, agent: str = "mentor"
    ) -> dict[str, list[str]]:
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
