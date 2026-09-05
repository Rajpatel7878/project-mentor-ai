"""Client Intake and Template Recommendation Service for Project Mentor AI.

Analyzes business problem descriptions, requirements, and constraints to recommend
the optimal agent template architecture (Customer-Facing, Internal Ops, Knowledge/RAG,
or Multi-Agent Orchestration) with transparent token budgeting and cost projections.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

CLIENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "customer_facing": {
        "id": "customer_facing",
        "name": "Customer-Facing Assistant",
        "tagline": "24/7 Autonomous Client Inquiries, Lead Triage & Support",
        "description": (
            "Designed for external customer interactions. Handles incoming website inquiries, "
            "qualifies sales leads, answers product FAQs with verified context, and logs tickets."
        ),
        "primary_agents": ["marketing", "mentor"],
        "recommended_tools": ["RAG Knowledge Base", "Lead Capture Webhook", "CRM Sync"],
        "setup_time": "1 - 2 business days",
        "monthly_token_estimate": 1_500_000,
        "gemini_monthly_cost_usd": 0.35,
        "gpt4_monthly_cost_usd": 15.00,
        "key_benefits": [
            "Instant 24/7 response time under 1.5 seconds",
            "Consistent brand voice aligned with marketing guidelines",
            "97% cost reduction compared to proprietary cloud LLMs",
            "Zero hallucination on product specs via RAG grounding",
        ],
        "keywords": [
            "customer", "client", "support", "sales", "leads", "inquiry",
            "website", "ticket", "external", "chat widget", "helpdesk", "faq"
        ],
    },
    "internal_ops": {
        "id": "internal_ops",
        "name": "Internal Operations & Automation Copilot",
        "tagline": "Automated Standups, Sprint Hygiene & Infrastructure Telemetry",
        "description": (
            "Empowers internal engineering and operations teams. Automates daily standup synthesis, "
            "tracks sprint blockers, executes verified system commands, and monitors IoT/host health."
        ),
        "primary_agents": ["operations", "pm", "engineer"],
        "recommended_tools": ["System Control Service", "IoT Device Bridge", "Local Host Telemetry"],
        "setup_time": "2 - 3 business days",
        "monthly_token_estimate": 2_500_000,
        "gemini_monthly_cost_usd": 0.65,
        "gpt4_monthly_cost_usd": 25.00,
        "key_benefits": [
            "Zero manual daily standup prep time for team leads",
            "Direct local host execution with granular safety confirmations",
            "Real-time CPU/RAM and smart device telemetry broadcasting",
            "100% on-premises data isolation for sensitive operational commands",
        ],
        "keywords": [
            "internal", "standup", "sprint", "task", "jira", "slack", "ops",
            "operation", "workflow", "automation", "system", "devops", "monitoring",
            "hardware", "device", "infrastructure"
        ],
    },
    "knowledge_rag": {
        "id": "knowledge_rag",
        "name": "Enterprise Knowledge & Document RAG",
        "tagline": "Instant Semantic Search Across SOPs, Technical Specs & PDFs",
        "description": (
            "Transforms scattered documents, compliance manuals, technical specifications, and JSON "
            "data into a high-speed, queryable local knowledge engine powered by ChromaDB."
        ),
        "primary_agents": ["analyst", "cto", "mentor"],
        "recommended_tools": ["ChromaDB Vector Store", "Hybrid BM25 Retrieval", "Multi-Format Ingestion"],
        "setup_time": "1 - 3 business days",
        "monthly_token_estimate": 4_000_000,
        "gemini_monthly_cost_usd": 1.10,
        "gpt4_monthly_cost_usd": 75.00,
        "key_benefits": [
            "No recurring vector DB subscription (self-hosted local ChromaDB)",
            "Hybrid lexical + dense vector search eliminates retrieval misses",
            "Instant drag-and-drop document updates via REST API",
            "Sub-second citation and reference retrieval",
        ],
        "keywords": [
            "document", "docs", "pdf", "manual", "search", "rag", "knowledge",
            "sop", "policy", "handbook", "retrieve", "information", "research",
            "compliance", "spec", "whitepaper"
        ],
    },
    "multi_agent_orchestration": {
        "id": "multi_agent_orchestration",
        "name": "JARVIS Full-Stack Multi-Agent Council",
        "tagline": "Complete Autonomous Executive Team (CTO, PM, VC, Marketing, Ops)",
        "description": (
            "The flagship enterprise configuration. LangGraph coordinates an entire council of "
            "specialized AI agents capable of strategic roadmapping, technical architecture, "
            "fundraising pitch deck review, and end-to-end task execution."
        ),
        "primary_agents": ["mentor", "cto", "pm", "marketing", "vc", "engineer", "operations", "analyst"],
        "recommended_tools": [
            "LangGraph StateGraph", "AgentRegistry", "RAG Engine",
            "IoT Bridge", "System Control", "Analytics Tracker"
        ],
        "setup_time": "3 - 5 business days",
        "monthly_token_estimate": 6_000_000,
        "gemini_monthly_cost_usd": 1.75,
        "gpt4_monthly_cost_usd": 150.00,
        "key_benefits": [
            "Seamless score-based routing to specialized domain experts",
            "Full memory retention across sessions (Firestore or Local JSON fallback)",
            "Live cost and token transparency dashboard for stakeholder reporting",
            "Over 98% savings compared to multi-agent GPT-4 enterprise setups",
        ],
        "keywords": [
            "executive", "council", "strategy", "cto", "vc", "fundraising",
            "architecture", "multi-agent", "all-in-one", "scale", "orchestration",
            "mentor", "complete", "everything", "full-stack", "complex"
        ],
    },
}


class IntakeService:
    """Service to analyze client business requirements and recommend agent templates."""

    def __init__(self) -> None:
        self.templates = CLIENT_TEMPLATES

    def list_templates(self) -> list[dict[str, Any]]:
        """Return list of all available templates without keyword internals."""
        return [
            {k: v for k, v in tpl.items() if k != "keywords"}
            for tpl in self.templates.values()
        ]

    def get_template(self, template_id: str) -> dict[str, Any] | None:
        """Get specific template details by ID."""
        tpl = self.templates.get(template_id)
        if not tpl:
            return None
        return {k: v for k, v in tpl.items() if k != "keywords"}

    def analyze(self, profile: dict[str, Any]) -> dict[str, Any]:
        """Analyze client problem profile and return template recommendation with ROI projections.
        
        Expected profile fields:
          - company_name: str
          - problem_statement: str
          - primary_goal: str (optional)
          - current_tools: list[str] or str (optional)
          - team_size: str (optional)
        """
        problem = str(profile.get("problem_statement", "")).lower()
        goal = str(profile.get("primary_goal", "")).lower()
        combined_text = f"{problem} {goal}"

        scores: dict[str, int] = {t_id: 0 for t_id in self.templates}

        for t_id, tpl in self.templates.items():
            for kw in tpl["keywords"]:
                if kw in combined_text:
                    scores[t_id] += 1

        # Check for multi-agent indicators (broad problem with multiple facets)
        has_tech = any(k in combined_text for k in ["code", "tech", "architecture", "cto"])
        has_business = any(k in combined_text for k in ["sales", "investor", "vc", "marketing"])
        has_ops = any(k in combined_text for k in ["ops", "standup", "sprint", "manage"])

        if sum([has_tech, has_business, has_ops]) >= 2:
            scores["multi_agent_orchestration"] += 3

        # Select highest scoring template, defaulting to multi_agent_orchestration if tied at 0
        best_id = max(scores, key=lambda k: scores[k])
        if scores[best_id] == 0:
            best_id = "multi_agent_orchestration"

        matched = self.templates[best_id]
        clean_matched = {k: v for k, v in matched.items() if k != "keywords"}

        # Calculate ROI projections
        gemini_cost = clean_matched["gemini_monthly_cost_usd"]
        gpt4_cost = clean_matched["gpt4_monthly_cost_usd"]
        monthly_savings = round(gpt4_cost - gemini_cost, 2)
        annual_savings = round(monthly_savings * 12, 2)
        savings_pct = round((monthly_savings / gpt4_cost) * 100, 1)

        company = profile.get("company_name", "Valued Client")

        rationale = (
            f"Based on {company}'s requirements focusing on '{problem[:80]}...', "
            f"the {clean_matched['name']} delivers the fastest path to value. "
            f"It activates {', '.join(clean_matched['primary_agents'])} with integrated "
            f"{', '.join(clean_matched['recommended_tools'])}, eliminating manual overhead "
            f"while cutting API costs by {savings_pct}%."
        )

        roadmap = [
            f"Phase 1: Ingest {company}'s domain knowledge and SOPs into local ChromaDB RAG",
            f"Phase 2: Configure swappable agents ({', '.join(clean_matched['primary_agents'])}) with custom tone guidelines",
            f"Phase 3: Connect required integration points ({', '.join(clean_matched['recommended_tools'])})",
            "Phase 4: Run end-to-end sandbox verification and live cost tracking audit",
            "Phase 5: Deploy via Docker Compose with local persistent storage",
        ]

        return {
            "company_name": company,
            "recommended_template": clean_matched,
            "fit_score": min(98, 70 + (scores[best_id] * 5)),
            "rationale": rationale,
            "roi_projections": {
                "monthly_tokens": clean_matched["monthly_token_estimate"],
                "gemini_monthly_cost_usd": gemini_cost,
                "gpt4_equivalent_monthly_usd": gpt4_cost,
                "monthly_savings_usd": monthly_savings,
                "annual_savings_usd": annual_savings,
                "savings_percentage": savings_pct,
            },
            "implementation_roadmap": roadmap,
            "all_scores": scores,
        }


# Global singleton instance
intake_service = IntakeService()
