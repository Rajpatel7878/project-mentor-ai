"""Proactive intelligence: standups, sprint planning, documentation."""

from datetime import datetime

from app.services.gemini import GeminiService
from app.services.memory import MemoryService


class ProactiveService:
    """Generate standups, sprint plans, and proactive suggestions."""

    def __init__(self, gemini: GeminiService, memory: MemoryService):
        self.gemini = gemini
        self.memory = memory

    async def generate_standup(self, session_id: str = "default") -> str:
        history = await self.memory.get_conversation_history(session_id, limit=30)
        decisions = await self.memory.get_recent_decisions(5)

        context = f"Date: {datetime.now().strftime('%A, %B %d, %Y')}\n"
        context += "Recent conversations:\n"
        for msg in history[-10:]:
            context += f"- [{msg.get('role')}] {msg.get('content', '')[:200]}\n"
        context += "\nRecent decisions:\n"
        for d in decisions:
            context += f"- {d.get('decision', '')}\n"

        prompt = f"""Generate a daily standup summary based on this project activity.
Include: What was accomplished, What's planned today, Blockers/Risks.
Format as a concise standup report addressed to the user as 'sir'.

{context}"""

        return await self.gemini.generate(prompt, agent="pm")

    async def generate_sprint_plan(self, goals: str) -> str:
        prompt = f"""Create a 2-week sprint plan for these goals: {goals}
Include: User stories, task breakdown, priorities, acceptance criteria.
Address the user as 'sir'. Be specific and actionable."""
        return await self.gemini.generate(prompt, agent="pm")

    async def generate_documentation(self, topic: str, session_id: str = "default") -> str:
        history = await self.memory.get_conversation_history(session_id, limit=20)
        context = "\n".join(f"{m.get('role')}: {m.get('content', '')[:300]}" for m in history)
        prompt = f"""Generate technical documentation for: {topic}
Based on project context below. Include overview, setup, usage, and API reference if applicable.

Project context:
{context}"""
        return await self.gemini.generate(prompt, agent="cto")
