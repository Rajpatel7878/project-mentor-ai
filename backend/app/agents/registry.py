"""Swappable Agent Registry for Project Mentor AI.

Enables dynamic, modular registration of specialized domain agents without
modifying core routing logic or LangGraph orchestration graphs.
"""

from dataclasses import dataclass, field
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentSpec:
    """Specification for a domain agent."""

    name: str
    display_name: str
    role_description: str
    system_prompt: str
    keywords: list[str] = field(default_factory=list)
    default_follow_ups: list[str] = field(default_factory=list)
    default_suggestions: list[str] = field(default_factory=list)
    category: str = "general"  # e.g. "leadership", "technical", "product", "growth", "operations"
    color_scheme: str = "cyan"  # Badge color theme for UI

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "role_description": self.role_description,
            "category": self.category,
            "color_scheme": self.color_scheme,
            "keywords": self.keywords,
            "follow_up_questions": self.default_follow_ups,
            "suggestions": self.default_suggestions,
        }


class AgentRegistry:
    """Central registry and router for all swappable agent personas."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentSpec] = {}
        self._register_default_agents()

    def register(self, spec: AgentSpec) -> None:
        """Register a new swappable agent specification."""
        self._agents[spec.name.lower()] = spec
        logger.info("Registered agent: %s (%s)", spec.name, spec.display_name)

    def unregister(self, name: str) -> None:
        """Remove an agent from the registry."""
        self._agents.pop(name.lower(), None)

    def get(self, name: str) -> Optional[AgentSpec]:
        """Retrieve an agent specification by name."""
        return self._agents.get(name.lower())

    def list_agents(self) -> list[AgentSpec]:
        """Return all registered agent specifications."""
        return list(self._agents.values())

    def get_prompt(self, name: str) -> str:
        """Get the system prompt for a specified agent, falling back to mentor."""
        agent = self.get(name) or self.get("mentor")
        return agent.system_prompt if agent else "You are a helpful AI mentor."

    def get_follow_ups(self, name: str) -> dict[str, list[str]]:
        """Retrieve default follow-up questions and suggestions for an agent."""
        agent = self.get(name) or self.get("mentor")
        if agent:
            return {
                "follow_up_questions": agent.default_follow_ups,
                "suggestions": agent.default_suggestions,
            }
        return {
            "follow_up_questions": ["What aspect would you like to explore further, sir?"],
            "suggestions": ["Review your daily priority tasks."],
        }

    def route(self, message: str) -> str:
        """Score-based keyword router: select the agent with the highest keyword relevance."""
        msg = message.lower()
        scores: dict[str, int] = {}
        for name, spec in self._agents.items():
            if name == "mentor":
                continue  # Mentor is the fallback coordinator
            # Match word or phrase in message
            count = sum(1 for k in spec.keywords if k in msg)
            if count > 0:
                scores[name] = count

        if scores:
            # Return agent with highest matching keyword count
            return max(scores, key=lambda a: scores[a])

        return "mentor"

    def _register_default_agents(self) -> None:
        """Register the built-in 8 Jarvis specialist agents."""

        # 1. Mentor Agent (Core Coordinator)
        self.register(
            AgentSpec(
                name="mentor",
                display_name="Mentor Agent",
                role_description="Executive advisor orchestrating cross-domain guidance, high-level strategy, and holistic mentorship.",
                system_prompt="You are the Mentor Agent — orchestrate guidance across all technical, business, and operational domains with wisdom, British elegance, and clarity.",
                category="leadership",
                color_scheme="cyan",
                keywords=[],
                default_follow_ups=[
                    "Would you like to break this into actionable strategic milestones, sir?",
                    "What is the primary constraint or bottleneck we should tackle first?",
                ],
                default_suggestions=[
                    "Document today's strategic decisions in your project knowledge base.",
                    "Focus on the highest-leverage task on your priority list.",
                ],
            )
        )

        # 2. CTO Agent
        self.register(
            AgentSpec(
                name="cto",
                display_name="CTO Agent",
                role_description="Chief Technology Officer overseeing software architecture, code reviews, DevOps, and engineering decisions.",
                system_prompt="You are the CTO Agent — expert in software architecture, scalable systems, code quality, database engineering, DevOps, and technical decisions.",
                category="technical",
                color_scheme="purple",
                keywords=["code", "architecture", "api", "database", "deploy", "bug", "test", "docker", "cloud", "backend", "frontend"],
                default_follow_ups=[
                    "Should we inspect system error logs and test coverage, sir?",
                    "Would you like to review the microservice architecture and database schemas?",
                ],
                default_suggestions=[
                    "Run the automated test suite to verify system health.",
                    "Inspect database connection pools and endpoint latency.",
                ],
            )
        )

        # 3. PM Agent
        self.register(
            AgentSpec(
                name="pm",
                display_name="Product Manager Agent",
                role_description="Product management specialist leading feature prioritization, sprint roadmaps, and user experience.",
                system_prompt="You are the PM Agent — expert in product strategy, roadmap planning, sprint prioritization, user personas, and agile feature delivery.",
                category="product",
                color_scheme="blue",
                keywords=["feature", "roadmap", "sprint", "task", "priority", "user story", "backlog", "mvp", "timeline"],
                default_follow_ups=[
                    "Should we prioritize these backlog items for the current sprint, sir?",
                    "Would you like me to draft user acceptance criteria for this feature?",
                ],
                default_suggestions=[
                    "Update roadmap milestones to reflect current progress.",
                    "Break down the architectural requirements into epics.",
                ],
            )
        )

        # 4. Marketing Agent
        self.register(
            AgentSpec(
                name="marketing",
                display_name="Marketing & Growth Agent",
                role_description="Go-to-market strategist focusing on brand positioning, user acquisition, and launch campaigns.",
                system_prompt="You are the Marketing Agent — expert in go-to-market strategy, brand positioning, content marketing, SEO, and user acquisition campaigns.",
                category="growth",
                color_scheme="pink",
                keywords=["marketing", "brand", "launch", "social", "campaign", "seo", "content", "traffic", "acquisition", "conversion"],
                default_follow_ups=[
                    "Shall I outline the multi-channel launch distribution plan, sir?",
                    "Would you like to craft a refined value proposition statement for your audience?",
                ],
                default_suggestions=[
                    "Define target customer personas and core messaging pillars.",
                    "Draft an executive release announcement for early adopters.",
                ],
            )
        )

        # 5. VC Agent
        self.register(
            AgentSpec(
                name="vc",
                display_name="Venture Capital & Finance Agent",
                role_description="Investment and financial strategist analyzing unit economics, fundraising pitch decks, and business models.",
                system_prompt="You are the VC Agent — expert in business model design, financial modeling, unit economics, investor decks, and seed/Series A fundraising.",
                category="growth",
                color_scheme="emerald",
                keywords=["funding", "investor", "revenue", "business model", "pitch", "vc", "valuation", "fundraising", "burn rate", "cap table"],
                default_follow_ups=[
                    "Should we evaluate the unit economics and runway projections, sir?",
                    "Would you like to rehearse pitch responses for prospective investors?",
                ],
                default_suggestions=[
                    "Structure a 10-slide executive pitch deck outline.",
                    "Refine your defensibility and competitive moat articulation.",
                ],
            )
        )

        # 6. Engineer & IoT Agent
        self.register(
            AgentSpec(
                name="engineer",
                display_name="Engineer & IoT Agent",
                role_description="Hardware automation and IoT diagnostic engineer managing physical devices, telemetry, and system control.",
                system_prompt="You are the Engineer & IoT Agent — expert in hardware automation, device diagnostics, protocols (MQTT/Home Assistant), and physical system health.",
                category="technical",
                color_scheme="amber",
                keywords=["light", "thermostat", "device", "iot", "temperature", "switch", "relay", "lock door", "hardware", "diagnostic", "sensor"],
                default_follow_ups=[
                    "Would you like to run full hardware diagnostics on all connected units, sir?",
                    "Should I adjust thermal, lighting, or power relay thresholds?",
                ],
                default_suggestions=[
                    "Monitor live CPU and RAM allocation on the IoT console.",
                    "Verify peripheral actuator states and failover protocols.",
                ],
            )
        )

        # 7. Operations & Scheduling Agent
        self.register(
            AgentSpec(
                name="operations",
                display_name="Operations & Scheduling Agent",
                role_description="Workflow and productivity coordinator organizing daily standups, agenda items, and operational routines.",
                system_prompt="You are the Operations & Scheduling Agent — expert in workflow automation, daily standup synthesis, meeting agendas, and productivity routines.",
                category="operations",
                color_scheme="indigo",
                keywords=["schedule", "calendar", "standup", "sprint plan", "meeting", "reminder", "agenda", "break", "routine", "workflow"],
                default_follow_ups=[
                    "Shall I compile today's automated standup summary for the team, sir?",
                    "Would you like me to set a focused productivity timer for this sprint?",
                ],
                default_suggestions=[
                    "Review your daily milestones and open blockers.",
                    "Generate an agenda briefing for your next strategy session.",
                ],
            )
        )

        # 8. Analyst Agent
        self.register(
            AgentSpec(
                name="analyst",
                display_name="Analyst & RAG Synthesis Agent",
                role_description="Information synthesis and intelligence researcher querying knowledge base documents and synthesizing data.",
                system_prompt="You are the Analyst Agent — expert in cross-document RAG summarization, data extraction, research synthesis, and executive briefing reports.",
                category="technical",
                color_scheme="teal",
                keywords=["synthesize", "analyze document", "summary", "report", "extract", "knowledge base", "research", "rag", "findings"],
                default_follow_ups=[
                    "Would you like an executive summary of this data, sir?",
                    "Shall I query the knowledge base for related documents and technical specs?",
                ],
                default_suggestions=[
                    "Index additional reference PDFs or project specs in RAG.",
                    "Synthesize key performance metrics into an actionable project report.",
                ],
            )
        )


# Global singleton instance
agent_registry = AgentRegistry()
