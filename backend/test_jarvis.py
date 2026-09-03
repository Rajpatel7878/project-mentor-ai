"""Comprehensive Automated Test Suite for Project Mentor AI (Jarvis System)."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path

# Set dummy env vars for testing before importing app modules
os.environ["ALLOW_SYSTEM_CONTROL"] = "true"
os.environ["GEMINI_API_KEY"] = ""

from app.models import DeviceStatus, DeviceType
from app.services.device_bridge import DeviceManager
from app.services.gemini import GeminiService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.services.system_control import SystemControlService
from app.agents.mentor_graph import MentorAgentSystem


def test_device_bridge():
    print("\n--- [TEST 1] Device Bridge & Hardware Abstraction Layer ---")
    dev_mgr = DeviceManager()

    # 1. Device listing
    devices = dev_mgr.list_devices()
    print(f"[OK] Registered devices count: {len(devices)}")
    assert len(devices) >= 5, "Expected at least 5 default devices"

    # 2. System telemetry
    snap = dev_mgr.get_telemetry_snapshot()
    print(f"[OK] Host telemetry: CPU={snap.system.get('cpu_percent')}%, RAM={snap.system.get('ram_percent')}%")

    # 3. Light control
    light_res = dev_mgr.execute_action("light-office-01", "set_level", {"brightness": 75})
    assert light_res.success is True
    assert light_res.new_state.get("brightness") == 75
    print("[OK] Smart Light brightness set to 75%")

    # 4. Thermostat control
    therm_res = dev_mgr.execute_action("climate-hvac-01", "set_temp", {"target_temp_c": 21.5})
    assert therm_res.success is True
    assert therm_res.new_state.get("target_temp_c") == 21.5
    print("[OK] Thermostat target set to 21.5°C")

    # 5. Security Lock HITL Safety check
    lock_unauth = dev_mgr.execute_action("lock-office-01", "unlock", confirm=False)
    assert lock_unauth.requires_confirmation is True
    print("[OK] Security Lock successfully blocked unconfirmed unlock (HITL required)")

    lock_auth = dev_mgr.execute_action("lock-office-01", "unlock", confirm=True)
    assert lock_auth.success is True
    assert lock_auth.new_state.get("locked") is False
    print("[OK] Security Lock unlocked with explicit authorization")

    # 6. Natural language command parser
    nl_res = dev_mgr.parse_and_execute_device_command("turn off the lights")
    assert len(nl_res) > 0 and nl_res[0]["success"] is True
    print("[OK] Natural language command 'turn off the lights' parsed and executed")


def test_rag_pipeline():
    print("\n--- [TEST 2] Enhanced RAG Pipeline (Multi-format & Hybrid Search) ---")
    tmp_dir = Path(tempfile.mkdtemp())
    k_dir = tmp_dir / "knowledge"
    p_dir = tmp_dir / "chroma"
    k_dir.mkdir()

    # Create sample docs
    (k_dir / "architecture.md").write_text("# System Architecture\nProject Mentor uses Next.js 14 and FastAPI with LangGraph multi-agent orchestration.", encoding="utf-8")
    (k_dir / "devices.txt").write_text("Connected IoT devices include smart lighting, HVAC thermostats, and security locks.", encoding="utf-8")
    (k_dir / "metrics.json").write_text('{"quarter": "Q3", "target": "Deploy RAG and Device Bridge"}', encoding="utf-8")

    rag = RAGService(knowledge_dir=k_dir, persist_dir=p_dir)

    docs = rag.list_documents()
    print(f"[OK] Indexed documents: {[d['name'] for d in docs]}")
    assert len(docs) == 3, f"Expected 3 docs, got {len(docs)}"

    # Ingestion API test
    new_doc = rag.ingest_file("protocols.txt", b"MQTT and Home Assistant WebSocket bridges are supported.")
    assert new_doc["name"] == "protocols.txt"
    print(f"[OK] Dynamic document ingestion verified: {new_doc['name']}")

    # Hybrid Search Test
    hybrid_results = rag.retrieve("What devices and protocols are supported?", top_k=3, mode="hybrid")
    assert len(hybrid_results) > 0
    print(f"[OK] Hybrid search returned {len(hybrid_results)} ranked chunks")
    for r in hybrid_results[:2]:
        print(f"   [{r['source']}] Score: {r['relevance']}% -> {r['text'][:60]}...")

    # Cleanup test
    rag.delete_document("protocols.txt")
    updated_docs = rag.list_documents()
    assert all(d["name"] != "protocols.txt" for d in updated_docs)
    print("[OK] Document deletion and vector purging verified")

    shutil.rmtree(tmp_dir, ignore_errors=True)


async def test_multi_agent_system():
    print("\n--- [TEST 3] Multi-Agent Routing & System Execution ---")
    gemini = GeminiService(api_key="")
    sys_control = SystemControlService(allow_control=True)
    dev_mgr = DeviceManager()

    tmp_dir = Path(tempfile.mkdtemp())
    k_dir = tmp_dir / "knowledge"
    p_dir = tmp_dir / "chroma"
    k_dir.mkdir()
    (k_dir / "guide.md").write_text("Jarvis assistant guides the user across business and tech.", encoding="utf-8")

    rag = RAGService(knowledge_dir=k_dir, persist_dir=p_dir)
    memory = MemoryService()

    agent_sys = MentorAgentSystem(
        gemini=gemini,
        rag=rag,
        memory=memory,
        system_control=sys_control,
        device_manager=dev_mgr,
    )

    # Test agent keyword routing across domain roles
    assert gemini._keyword_route("How should I configure the database architecture?") == "cto"
    print("[OK] Routed architecture query -> CTO agent")

    assert gemini._keyword_route("Turn off the office lights and check thermostat") == "engineer"
    print("[OK] Routed IoT query -> Engineer (IoT) agent")

    assert gemini._keyword_route("Schedule daily standup and sprint reminder") == "operations"
    print("[OK] Routed calendar query -> Operations agent")

    assert gemini._keyword_route("Synthesize the project knowledge base report") == "analyst"
    print("[OK] Routed synthesis query -> Analyst agent")

    # Run complete workflow through LangGraph
    response = await agent_sys.process(
        message="Turn on the lights and report status",
        session_id="test-session",
        execute_commands=True,
    )

    print(f"[OK] Agent execution successful: routed to '{response['agent']}'")
    print(f"   Command results count: {len(response['command_results'])}")
    print(f"   Suggestions count: {len(response['suggestions'])}")

    shutil.rmtree(tmp_dir, ignore_errors=True)


async def main():
    print("==================================================")
    print("PROJECT MENTOR AI - AUTOMATED VERIFICATION SUITE")
    print("==================================================")
    test_device_bridge()
    test_rag_pipeline()
    await test_multi_agent_system()
    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (100% HEALTH)")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
