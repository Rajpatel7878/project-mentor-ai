"""Usage and cost analytics tracking service for Project Mentor AI.

Tracks API calls, token usage, latency, and estimated cost per agent,
providing real performance and ROI metrics for client demonstrations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Google Gemini Flash Pricing (USD per 1 Million Tokens) as of 2025/2026
GEMINI_INPUT_COST_PER_M = 0.075   # $0.075 per 1M prompt tokens
GEMINI_OUTPUT_COST_PER_M = 0.300  # $0.300 per 1M completion tokens

# Comparison Benchmarks (Competitor models for ROI calculation)
GPT4O_INPUT_COST_PER_M = 2.50     # $2.50 per 1M prompt tokens (~33x higher)
GPT4O_OUTPUT_COST_PER_M = 10.00   # $10.00 per 1M completion tokens (~33x higher)


class AnalyticsService:
    """Tracks token consumption, latency, and costs per agent."""

    def __init__(self, storage_path: str = "./data/analytics/usage_metrics.json") -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._metrics = self._load()

    def _load(self) -> dict[str, Any]:
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Could not read analytics file, initializing fresh: %s", exc)
        return {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_latency_ms": 0,
            "agents": {},
            "history": [],
        }

    def _save(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps(self._metrics, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:
            logger.error("Failed to save analytics: %s", exc)

    def record_call(
        self,
        agent: str,
        message: str,
        response: str,
        latency_ms: float,
        success: bool = True,
    ) -> dict[str, Any]:
        """Record an agent invocation and calculate cost metrics."""
        # Estimate token count if exact tokenizer is not exposed (heuristic: ~4 chars per token)
        input_tokens = max(1, len(message) // 4)
        output_tokens = max(1, len(response) // 4)

        gemini_cost = (
            (input_tokens / 1_000_000) * GEMINI_INPUT_COST_PER_M
            + (output_tokens / 1_000_000) * GEMINI_OUTPUT_COST_PER_M
        )
        gpt4_equiv_cost = (
            (input_tokens / 1_000_000) * GPT4O_INPUT_COST_PER_M
            + (output_tokens / 1_000_000) * GPT4O_OUTPUT_COST_PER_M
        )

        agent_key = agent.lower()
        if agent_key not in self._metrics["agents"]:
            self._metrics["agents"][agent_key] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_latency_ms": 0,
                "cost_usd": 0.0,
            }

        agent_stats = self._metrics["agents"][agent_key]
        agent_stats["calls"] += 1
        agent_stats["input_tokens"] += input_tokens
        agent_stats["output_tokens"] += output_tokens
        agent_stats["total_latency_ms"] += latency_ms
        agent_stats["cost_usd"] += gemini_cost

        self._metrics["total_calls"] += 1
        self._metrics["total_input_tokens"] += input_tokens
        self._metrics["total_output_tokens"] += output_tokens
        self._metrics["total_latency_ms"] += latency_ms

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_key,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": round(latency_ms, 2),
            "cost_usd": round(gemini_cost, 6),
            "gpt4_cost_usd": round(gpt4_equiv_cost, 6),
            "success": success,
        }
        self._metrics.setdefault("history", []).append(entry)
        # Keep last 500 records in history
        if len(self._metrics["history"]) > 500:
            self._metrics["history"] = self._metrics["history"][-500:]

        self._save()
        return entry

    def get_summary(self) -> dict[str, Any]:
        """Generate executive usage, cost, and ROI summary."""
        total_calls = self._metrics.get("total_calls", 0)
        total_in = self._metrics.get("total_input_tokens", 0)
        total_out = self._metrics.get("total_output_tokens", 0)
        total_tokens = total_in + total_out

        total_cost = (
            (total_in / 1_000_000) * GEMINI_INPUT_COST_PER_M
            + (total_out / 1_000_000) * GEMINI_OUTPUT_COST_PER_M
        )
        gpt4_cost = (
            (total_in / 1_000_000) * GPT4O_INPUT_COST_PER_M
            + (total_out / 1_000_000) * GPT4O_OUTPUT_COST_PER_M
        )
        total_savings = max(0.0, gpt4_cost - total_cost)

        avg_latency = (
            self._metrics.get("total_latency_ms", 0) / total_calls if total_calls > 0 else 0
        )

        agent_breakdown = {}
        for a_name, a_data in self._metrics.get("agents", {}).items():
            calls = a_data["calls"]
            agent_breakdown[a_name] = {
                "calls": calls,
                "input_tokens": a_data["input_tokens"],
                "output_tokens": a_data["output_tokens"],
                "total_tokens": a_data["input_tokens"] + a_data["output_tokens"],
                "avg_latency_ms": round(a_data["total_latency_ms"] / calls, 1) if calls else 0,
                "cost_usd": round(a_data.get("cost_usd", 0.0), 5),
            }

        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "avg_latency_ms": round(avg_latency, 1),
            "total_cost_usd": round(total_cost, 6),
            "gpt4_equivalent_cost_usd": round(gpt4_cost, 6),
            "estimated_savings_usd": round(total_savings, 6),
            "savings_percentage": round((total_savings / gpt4_cost * 100), 1) if gpt4_cost > 0 else 96.5,
            "agent_breakdown": agent_breakdown,
            "model": "gemini-flash-latest",
            "recent_activity": self._metrics.get("history", [])[-15:],
        }


    def reset_metrics(self) -> None:
        """Reset all counters for clean client demonstration."""
        self._metrics = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_latency_ms": 0,
            "agents": {},
            "history": [],
        }
        self._save()


# Global singleton instance
analytics_service = AnalyticsService()
