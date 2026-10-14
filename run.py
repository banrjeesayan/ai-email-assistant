import uvicorn
import os
import signal
import subprocess
import sys

def free_port(port: int):
    """Kill any process holding the given port before starting."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split()
        for pid in pids:
            if pid:
                os.kill(int(pid), signal.SIGKILL)
                print(f"[startup] Killed stale process {pid} on port {port}")
    except Exception:
        pass  # Nothing to kill

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    free_port(port)  # Auto-clear port before starting
    print(f"[startup] Starting backend on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
