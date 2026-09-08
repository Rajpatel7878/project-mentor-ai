"""Interactive Guided Action Workflow Service for Project Mentor AI.

Empowers JARVIS to proactively assist the user through multi-step workflows
by asking targeted clarifying questions, structuring action plans, and automating tasks.
"""

import logging
from typing import Any

from app.models import ActionWorkflow

logger = logging.getLogger(__name__)

BUILTIN_ACTION_WORKFLOWS: list[dict[str, Any]] = [
    {
        "id": "sprint_planning",
        "title": "Guided Sprint & Milestone Planning",
        "tagline": "Step-by-step goal breakdown, blocker identification, and velocity targets.",
        "category": "productivity",
        "icon": "Calendar",
        "assigned_agent": "pm",
        "starter_prompt": (
            "Sir, I have initialized our Guided Sprint Planning protocol. To ensure our objectives "
            "are razor-sharp, let us address this systematically:\n\n"
            "1. **Primary Milestone**: What is the single most critical feature or capability to deliver this sprint?\n"
            "2. **Blockers & Dependencies**: Are there any external APIs, credentials, or architectural dependencies we must unblock?\n"
            "3. **Velocity & Scope**: What is our expected timeline or team capacity?\n\n"
            "Whenever you are ready, please share your thoughts on the primary milestone."
        ),
        "guiding_questions": [
            "What is your primary milestone or deliverable for this sprint cycle, sir?",
            "Are there any cross-functional dependencies or technical blockers we need to anticipate?",
            "What is our planned timeline and target velocity for deployment?",
        ],
    },
    {
        "id": "architecture_review",
        "title": "Deep Architecture & Code Review",
        "tagline": "Scalability audit, caching strategies, database schema, and resilience.",
        "category": "engineering",
        "icon": "Cpu",
        "assigned_agent": "cto",
        "starter_prompt": (
            "Standing by for architectural assessment, sir. Let us review the technical parameters:\n\n"
            "1. **System Boundaries**: Which service, microservice, or API schema are we optimizing?\n"
            "2. **Throughput & Latency**: What are our peak concurrent connections and SLA latency targets (e.g. < 50ms)?\n"
            "3. **Data & Cache Layer**: Should we introduce an in-memory caching tier (Redis/LRU) or partition the storage engine?\n\n"
            "Which component shall we analyze first?"
        ),
        "guiding_questions": [
            "Which service, database schema, or pipeline would you like us to architect today, sir?",
            "What are your expected request throughput and latency thresholds?",
            "Should we design for local on-premises deployment or hybrid cloud infrastructure?",
        ],
    },
    {
        "id": "pitch_deck_generator",
        "title": "Investor Pitch & Unit Economics",
        "tagline": "TAM estimation, LTV/CAC ratios, competitive moat, and funding ask.",
        "category": "growth",
        "icon": "TrendingUp",
        "assigned_agent": "vc",
        "starter_prompt": (
            "Ready to pressure-test the investment thesis, sir. Tier-1 venture funds will scrutinize three key pillars:\n\n"
            "1. **The Unfair Advantage**: What is our unique technological moat that competitors cannot easily clone?\n"
            "2. **Unit Economics**: What is our estimated customer acquisition cost (CAC) versus projected lifetime value (LTV)?\n"
            "3. **The Capital Allocation**: How much funding are we targeting, and what milestone does it achieve before next raise?\n\n"
            "Tell me about your core value proposition to begin."
        ),
        "guiding_questions": [
            "What is the core customer problem, and who is your ideal customer profile (ICP)?",
            "What is your proposed monetization model and current gross margins?",
            "How much capital are you seeking, and what runway milestone does this unlock?",
        ],
    },
    {
        "id": "system_health_audit",
        "title": "Complete System & IoT Diagnostic",
        "tagline": "Host hardware telemetry, IoT peripheral check, and vector memory purge.",
        "category": "operations",
        "icon": "ShieldCheck",
        "assigned_agent": "engineer",
        "starter_prompt": (
            "Initiating full diagnostic scan sequence, sir. Telemetry sensors are standing by:\n\n"
            "1. **Host Workstation**: CPU load, memory saturation, and storage integrity.\n"
            "2. **Connected Hardware**: Smart lighting halo, HVAC thermostat, security access lock, and smartphone companion.\n"
            "3. **Cognitive Pipelines**: Local ChromaDB vector collections and response latency.\n\n"
            "Shall I execute a comprehensive diagnostic sweep across all connected systems right now?"
        ),
        "guiding_questions": [
            "Shall I scan host CPU/RAM, IoT devices, or vector RAG caches?",
            "Would you like me to cycle the ambient lighting and smart power relays to verify response latency?",
            "Should I test the emergency security lock and failover paths?",
        ],
    },
    {
        "id": "phone_remote_control",
        "title": "Smartphone Companion & Locator",
        "tagline": "Locate phone with high-volume alarm, inspect battery, or sync clipboard.",
        "category": "device",
        "icon": "Smartphone",
        "assigned_agent": "engineer",
        "starter_prompt": (
            "Smartphone companion bridge connected and operational, sir. I have active telemetry from your mobile device.\n\n"
            "Available rapid triggers:\n"
            "- **Find My Phone**: Ring your phone at 100% volume to locate it immediately.\n"
            "- **Security Lock**: Lock the display remotely.\n"
            "- **Flashlight**: Toggle the rear LED torch.\n"
            "- **Clipboard Sync**: Send code, links, or notes directly to your phone.\n\n"
            "What would you like me to dispatch to your phone, sir?"
        ),
        "guiding_questions": [
            "Would you like me to ring your smartphone at maximum volume, or inspect its telemetry status?",
            "Shall I copy your recent terminal command or notes to your phone clipboard?",
            "Would you like me to send a high-priority push reminder to your lock screen?",
        ],
    },
]


class ActionWorkflowService:
    """Service managing interactive guided action workflows."""

    def __init__(self):
        self._workflows = {w["id"]: ActionWorkflow(**w) for w in BUILTIN_ACTION_WORKFLOWS}

    def list_workflows(self) -> list[ActionWorkflow]:
        """Return all available interactive guided workflows."""
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> ActionWorkflow | None:
        """Get a specific guided action workflow by ID."""
        return self._workflows.get(workflow_id)

    def trigger_workflow(self, workflow_id: str, user_context: str = "") -> dict[str, Any]:
        """Initiate an interactive guided action workflow, returning starter prompt and metadata."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            # Fallback to sprint planning
            workflow = self._workflows["sprint_planning"]

        prompt = workflow.starter_prompt
        if user_context:
            prompt = f"Context: {user_context}\n\n{prompt}"

        return {
            "workflow_id": workflow.id,
            "title": workflow.title,
            "assigned_agent": workflow.assigned_agent,
            "starter_prompt": prompt,
            "guiding_questions": workflow.guiding_questions,
        }


# Global singleton instance
action_workflow_service = ActionWorkflowService()
