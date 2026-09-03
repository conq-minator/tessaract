"""
Pipeline test script: Runs all files in `real things`, sends telemetry events,
and verifies Member 4 context & Member 5 Knowledge Graph concept extraction.
"""

import os
import subprocess
import json
import time
from datetime import datetime, timezone
import urllib.request
import urllib.parse


REAL_THINGS_DIR = r"c:\vibe coded projects\tessaract\real things"
CORE_EVENTS_URL = "http://localhost:9700/api/v1/events"
CORE_CONTEXT_URL = "http://localhost:9700/api/v1/context/current"
KG_URL = "http://localhost:9701/api/v1/knowledge/graph"
AUTH_TOKEN = "rQUSMHvr5MVgVdCH-b8seB7UbRYeykyJYjBzaZeN2Pk"


def post_event(file_path: str, command: str, exit_code: int):
    payload = {
        "event_id": f"test-evt-{int(time.time()*1000)}",
        "source": "vscode_sensor",
        "event_type": "terminal_command",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "command": command,
            "file_path": file_path,
            "exit_code": exit_code
        }
    }
    req = urllib.request.Request(
        CORE_EVENTS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_current_context():
    req = urllib.request.Request(CORE_CONTEXT_URL)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_knowledge_graph():
    req = urllib.request.Request(KG_URL, headers={"Authorization": f"Bearer {AUTH_TOKEN}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def run_pipeline_test():
    files = [
        ("01_binary_search_tree.py", ["python", os.path.join(REAL_THINGS_DIR, "01_binary_search_tree.py")]),
        ("02_matrix_dynamic_programming.py", ["python", os.path.join(REAL_THINGS_DIR, "02_matrix_dynamic_programming.py")]),
        ("03_async_task_worker_pool.py", ["python", os.path.join(REAL_THINGS_DIR, "03_async_task_worker_pool.py")]),
        ("04_lru_cache_linked_list.py", ["python", os.path.join(REAL_THINGS_DIR, "04_lru_cache_linked_list.py")]),
        ("05_memory_arena_allocator.py", ["python", os.path.join(REAL_THINGS_DIR, "05_memory_arena_allocator.py")]),
        ("06_event_emitter_pubsub.js", ["node", os.path.join(REAL_THINGS_DIR, "06_event_emitter_pubsub.js")]),
    ]

    print("=================================================================")
    print("[RUNNING TELEMETRY & KNOWLEDGE GRAPH PIPELINE TEST FOR REAL THINGS]")
    print("=================================================================")

    for filename, cmd in files:
        full_path = os.path.join(REAL_THINGS_DIR, filename)
        print(f"\n>> Executing: {filename}")
        t0 = time.time()
        res = subprocess.run(cmd, capture_output=True, text=True)
        dur = round((time.time() - t0) * 1000, 2)
        print(f"  Exit Code: {res.returncode} (took {dur}ms)")
        if res.returncode != 0:
            print(f"  Error: {res.stderr.strip()}")
        else:
            first_line = res.stdout.strip().split("\n")[0] if res.stdout else ""
            print(f"  Output preview: {first_line}")

        # Send Sensor Event to Member 4
        cmd_str = " ".join(cmd)
        post_event(file_path=full_path, command=cmd_str, exit_code=res.returncode)
        time.sleep(1.5)

        # Check Core Engine Context
        ctx = get_current_context()
        print(f"  * Core Engine Detected Topic: {ctx.get('topic')} | Friction: {ctx.get('friction_level')}")

    # Allow Member 5 to process all async updates
    time.sleep(1.0)

    print("\n=================================================================")
    print("[KNOWLEDGE GRAPH NODES ACCUMULATED IN MEMBER 5]")
    print("=================================================================")
    kg = get_knowledge_graph()
    nodes = kg.get("nodes", [])
    print(f"Total Concepts in Knowledge Graph: {len(nodes)}")
    for n in sorted(nodes, key=lambda x: (x.get("domain", ""), x.get("name", ""))):
        conf = round(n.get("confidence", 0) * 100)
        status = n.get("status")
        ev = n.get("evidence_count")
        print(f"  [{n.get('domain').upper():10}] {n.get('name'):32} | Mastery: {conf}% | Ev: {ev}x | Status: {status}")


if __name__ == "__main__":
    run_pipeline_test()
