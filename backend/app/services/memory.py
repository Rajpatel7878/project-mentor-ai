"""Firestore long-term memory service with local fallback."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MemoryService:
    """Store conversations, preferences, and project decisions."""

    def __init__(self, project_id: str = "", credentials_path: str = ""):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self._db = None
        self._local_path = Path("./data/memory/local_store.json")
        self._local_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_firestore()

    def _init_firestore(self) -> None:
        if not self.project_id:
            logger.info("Firestore project ID not set. Using local memory fallback.")
            return
        try:
            from google.cloud import firestore
            if self.credentials_path:
                import os
                os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", self.credentials_path)
            self._db = firestore.Client(project=self.project_id)
            logger.info("Firestore connected for project: %s", self.project_id)
        except Exception as exc:
            logger.warning("Firestore unavailable, using local fallback: %s", exc)
            self._db = None

    def _load_local(self) -> dict[str, Any]:
        if self._local_path.exists():
            return json.loads(self._local_path.read_text(encoding="utf-8"))
        return {"conversations": {}, "preferences": {}, "decisions": [], "metrics": {}}

    def _save_local(self, data: dict[str, Any]) -> None:
        self._local_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    async def save_message(self, session_id: str, role: str, content: str, agent: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        entry = {"role": role, "content": content, "agent": agent, "timestamp": datetime.utcnow().isoformat(), "metadata": metadata or {}}
        if self._db:
            try:
                self._db.collection("conversations").document(session_id).collection("messages").add(entry)
                return
            except Exception as exc:
                logger.warning("Firestore write failed: %s", exc)
        data = self._load_local()
        data.setdefault("conversations", {}).setdefault(session_id, []).append(entry)
        self._save_local(data)

    async def get_conversation_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        if self._db:
            try:
                docs = self._db.collection("conversations").document(session_id).collection("messages").order_by("timestamp").limit(limit).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as exc:
                logger.warning("Firestore read failed: %s", exc)
        data = self._load_local()
        return data.get("conversations", {}).get(session_id, [])[-limit:]

    async def get_preferences(self, user_id: str = "default") -> dict[str, Any]:
        defaults = {"name": "Sir", "voice_enabled": True, "wake_words": ["hey mentor", "jarvis"], "project_phase": "building", "theme": "holographic"}
        if self._db:
            try:
                doc = self._db.collection("users").document(user_id).get()
                if doc.exists:
                    return {**defaults, **doc.to_dict()}
            except Exception as exc:
                logger.warning("Firestore preferences read failed: %s", exc)
        data = self._load_local()
        return {**defaults, **data.get("preferences", {}).get(user_id, {})}

    async def save_preferences(self, user_id: str, preferences: dict[str, Any]) -> None:
        if self._db:
            try:
                self._db.collection("users").document(user_id).set(preferences, merge=True)
                return
            except Exception as exc:
                logger.warning("Firestore preferences write failed: %s", exc)
        data = self._load_local()
        data.setdefault("preferences", {})[user_id] = preferences
        self._save_local(data)

    async def save_decision(self, session_id: str, decision: str, context: str = "") -> None:
        entry = {"decision": decision, "context": context, "session_id": session_id, "timestamp": datetime.utcnow().isoformat()}
        if self._db:
            try:
                self._db.collection("decisions").add(entry)
                return
            except Exception as exc:
                logger.warning("Firestore decision write failed: %s", exc)
        data = self._load_local()
        data.setdefault("decisions", []).append(entry)
        self._save_local(data)

    async def get_recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        if self._db:
            try:
                docs = self._db.collection("decisions").order_by("timestamp", direction="DESCENDING").limit(limit).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as exc:
                logger.warning("Firestore decisions read failed: %s", exc)
        data = self._load_local()
        return data.get("decisions", [])[-limit:]

    async def get_metrics(self) -> dict[str, Any]:
        defaults = {"total_conversations": 0, "decisions_made": 0, "tasks_completed": 0, "project_phase": "building", "last_active": None}
        if self._db:
            try:
                doc = self._db.collection("metrics").document("project").get()
                if doc.exists:
                    return {**defaults, **doc.to_dict()}
            except Exception as exc:
                logger.warning("Firestore metrics read failed: %s", exc)
        data = self._load_local()
        return {**defaults, **data.get("metrics", {})}

    async def update_metrics(self, updates: dict[str, Any]) -> None:
        if self._db:
            try:
                self._db.collection("metrics").document("project").set(updates, merge=True)
                return
            except Exception as exc:
                logger.warning("Firestore metrics update failed: %s", exc)
        data = self._load_local()
        data.setdefault("metrics", {}).update(updates)
        data["metrics"]["last_active"] = datetime.utcnow().isoformat()
        self._save_local(data)
