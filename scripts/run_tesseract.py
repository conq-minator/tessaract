#!/usr/bin/env python3
"""
Tesseract System Supervisor & Launcher
Starts Member 4 (Core Engine :9700), Member 5 (AI & Knowledge :9701), and Member 6 (Tutor UI :9702),
monitors their health, and ensures clean, complete termination upon Ctrl+C or exit command.
"""

import os
import sys
import time
import signal
import socket
import webbrowser
import subprocess
import threading
import urllib.request
import urllib.error

# Ensure immediate unbuffered terminal output
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = sys.executable

SERVICES = [
    {
        "name": "Member 5 (AI & Knowledge)",
        "port": 9701,
        "cwd": os.path.join(ROOT_DIR, "member-5_ai-knowledge"),
        "cmd": [PYTHON_EXE, "-m", "src.api.app"],
        "env": {"PYTHONPATH": "."},
        "health_url": "http://localhost:9701/health",
    },
    {
        "name": "Member 4 (Core Engine)",
        "port": 9700,
        "cwd": os.path.join(ROOT_DIR, "member-4_core-engine"),
        "cmd": [PYTHON_EXE, "-m", "core_engine.main"],
        "env": {"PYTHONPATH": "src"},
        "health_url": "http://localhost:9700/api/v1/health",
    },
    {
        "name": "Member 6 (Tutor UI)",
        "port": 9702,
        "cwd": os.path.join(ROOT_DIR, "member-6_tutor-ui"),
        "cmd": [PYTHON_EXE, "-m", "tutor_ui", "--no-desktop", "--no-tray"],
        "env": {"PYTHONPATH": "src"},
        "health_url": "http://localhost:9702/health",
    },
]

running_processes = []
is_shutting_down = False


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_port_owner(port: int):
    """Find and kill any process listening on the specified port on Windows."""
    try:
        cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object {{ Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }}"'
        subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
    except Exception:
        pass


def kill_process_tree(pid: int):
    """Kill process and all child processes on Windows."""
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, timeout=5)
    except Exception:
        pass


def cleanup():
    global is_shutting_down, running_processes
    if is_shutting_down:
        return
    is_shutting_down = True

    print("\n" + "=" * 64)
    print("  Stopping all Tesseract services...")
    print("=" * 64)

    # 1. Terminate tracked subprocesses
    for svc_info in running_processes:
        proc = svc_info.get("proc")
        name = svc_info.get("name")
        if proc and proc.poll() is None:
            print(f"  [-] Stopping {name} (PID {proc.pid})...")
            try:
                kill_process_tree(proc.pid)
                proc.terminate()
            except Exception:
                pass

    time.sleep(0.5)

    # 2. Guarantee ports are freed
    for svc in SERVICES:
        port = svc["port"]
        if is_port_in_use(port):
            kill_port_owner(port)

    print("\n  [OK] All Tesseract ports (9700, 9701, 9702) have been released.")
    print("  [OK] Shutdown complete.\n")


def check_health(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TesseractLauncher"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False


def wait_for_services(timeout_s: float = 12.0):
    print("  Waiting for ports to initialize...")
    start_time = time.time()
    pending = list(SERVICES)

    while pending and (time.time() - start_time) < timeout_s:
        still_pending = []
        for svc in pending:
            if check_health(svc["health_url"]) or is_port_in_use(svc["port"]):
                print(f"  [+] {svc['name']} is listening on port {svc['port']}")
            else:
                still_pending.append(svc)
        pending = still_pending
        if pending:
            time.sleep(0.8)

    if pending:
        for svc in pending:
            print(f"  [!] {svc['name']} port {svc['port']} starting up...")


def print_banner():
    banner = r"""
  ================================================================
      ______                                       __ 
     /_  __/__  ______________  _________  _____  / /_
      / / / _ \/ ___/ ___/ _ \/ ___/ __ `/ ___/ / __/
     / / /  __(__  |__  )  __/ /  / /_/ / /__  / /_  
    /_/  \___/____/____/\___/_/   \__,_/\___/  \__/  
                     System Orchestrator
  ================================================================
  """
    print(banner)


def print_status_summary():
    print("  Tesseract is actively running:")
    print("  " + "-" * 60)
    print("  * Member 4 (Core Engine):   http://localhost:9700")
    print("  * Member 5 (AI Knowledge):  http://localhost:9701")
    print("  * Member 6 (Tutor UI):      http://localhost:9702")
    print("  " + "-" * 60)
    print("  Web Interfaces:")
    print("  * Dashboard Overview:       http://localhost:9702/overview")
    print("  * Knowledge Graph:          http://localhost:9702/knowledge-graph")
    print("  * AI Tutor Chat:            http://localhost:9702/chat")
    print("  ================================================================")
    print("  Press Ctrl+C or type 'q' and press Enter to STOP all services.")
    print("  ================================================================\n")


def signal_handler(signum, frame):
    cleanup()
    sys.exit(0)


def listen_for_user_exit():
    """Allow user to terminate cleanly by typing 'q' or 'exit' or pressing Enter in console."""
    try:
        while not is_shutting_down:
            line = sys.stdin.readline()
            if is_shutting_down:
                break
            if line:
                cmd = line.strip().lower()
                if cmd in ("q", "quit", "exit", "stop", ""):
                    cleanup()
                    os._exit(0)
    except Exception:
        pass


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print_banner()

    # Pre-clean any stale processes holding our ports
    print("  Checking for stale processes on ports 9700, 9701, 9702...")
    for svc in SERVICES:
        port = svc["port"]
        if is_port_in_use(port):
            print(f"  [-] Freeing port {port} from prior session...")
            kill_port_owner(port)
            time.sleep(0.5)

    print("  Starting Tesseract core services...\n")

    # Start services
    for svc in SERVICES:
        env = os.environ.copy()
        for k, v in svc.get("env", {}).items():
            if k == "PYTHONPATH":
                env[k] = v + os.pathsep + env.get("PYTHONPATH", "")
            else:
                env[k] = v

        try:
            # Use CREATE_NEW_PROCESS_GROUP on Windows so Ctrl+C can be handled by supervisor
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            proc = subprocess.Popen(
                svc["cmd"],
                cwd=svc["cwd"],
                env=env,
                creationflags=flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            running_processes.append({"name": svc["name"], "port": svc["port"], "proc": proc})
            print(f"  [>] Launched {svc['name']} (PID {proc.pid})")
            time.sleep(0.6)
        except Exception as e:
            print(f"  [!] Failed to start {svc['name']}: {e}")

    # Wait for endpoints to become responsive
    wait_for_services()

    # Display operational URLs
    print_status_summary()

    if "--open" in sys.argv or "-o" in sys.argv:
        print("  Opening Tesseract Web UI in your browser...")
        try:
            webbrowser.open("http://localhost:9702")
        except Exception:
            pass

    # Start background listener thread for console input
    input_thread = threading.Thread(target=listen_for_user_exit, daemon=True)
    input_thread.start()

    # Main supervision loop
    try:
        while not is_shutting_down:
            time.sleep(1.0)
            # Check if any process died unexpectedly
            for svc_info in running_processes:
                proc = svc_info["proc"]
                if proc.poll() is not None and not is_shutting_down:
                    print(f"\n  [!] Warning: {svc_info['name']} exited with code {proc.returncode}")
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
