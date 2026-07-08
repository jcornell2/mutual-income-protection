#!/usr/bin/env python3
"""One-command launcher for Mutual Income Protection."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
DEPS_MARKER = VENV_DIR / ".deps_installed"


def python_executable() -> str:
    if VENV_DIR.exists():
        if sys.platform == "win32":
            return str(VENV_DIR / "Scripts" / "python.exe")
        return str(VENV_DIR / "bin" / "python")
    return sys.executable


def pause_on_exit() -> None:
    if sys.platform == "win32":
        print("\nPress Enter to close this window...")
        try:
            input()
        except EOFError:
            pass


def ensure_venv() -> None:
    if VENV_DIR.exists():
        return
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])


def ensure_dependencies() -> None:
    if DEPS_MARKER.exists():
        return
    py = python_executable()
    print("Installing dependencies (first run only)...")
    subprocess.check_call([py, "-m", "pip", "install", "--upgrade", "pip"], stdout=subprocess.DEVNULL)
    subprocess.check_call([py, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    DEPS_MARKER.touch()


def ensure_env() -> None:
    if ENV_FILE.exists():
        return
    from cryptography.fernet import Fernet

    encryption_key = Fernet.generate_key().decode()
    admin_key = Fernet.generate_key().decode()[:32]
    example = ENV_EXAMPLE.read_text(encoding="utf-8")
    content = example.replace("your-fernet-key-here", encryption_key).replace(
        "change-me-to-a-strong-random-key", admin_key
    )
    ENV_FILE.write_text(content, encoding="utf-8")
    print(f"Created {ENV_FILE} with generated keys.")


def load_env() -> dict[str, str]:
    from dotenv import dotenv_values

    return {k: v for k, v in dotenv_values(ENV_FILE).items() if v is not None}


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, int(port)))
            return True
        except OSError:
            return False


def find_free_port(host: str, preferred: int) -> int:
    if port_is_free(host, preferred):
        return preferred
    for port in range(preferred + 1, preferred + 50):
        if port_is_free(host, port):
            print(f"  Port {preferred} is busy — using {port} instead.")
            return port
    raise RuntimeError(f"No free port found near {preferred}")


def wait_for_api(base_url: str, timeout: int = 30) -> bool:
    import httpx

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{base_url}/health", timeout=2.0).status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return False


def stop_processes(*processes: subprocess.Popen) -> None:
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def open_browsers(streamlit_port: int, api_base: str) -> None:
    try:
        webbrowser.open(f"http://127.0.0.1:{streamlit_port}")
        webbrowser.open(f"{api_base}/")
        webbrowser.open(f"{api_base}/apply")
    except Exception:
        pass


def main() -> None:
    api_proc: subprocess.Popen | None = None
    streamlit_proc: subprocess.Popen | None = None

    try:
        os.chdir(ROOT)
        ensure_venv()
        ensure_dependencies()
        ensure_env()

        env = load_env()
        py = python_executable()
        api_host = env.get("API_HOST", "127.0.0.1")
        api_port = find_free_port(api_host, int(env.get("API_PORT", "8000")))
        streamlit_port = find_free_port("127.0.0.1", int(env.get("STREAMLIT_PORT", "8501")))
        api_base = f"http://{api_host}:{api_port}"

        env_vars = os.environ.copy()
        env_vars.update(env)
        env_vars["API_BASE"] = api_base
        env_vars["ADMIN_API_KEY"] = env.get("ADMIN_API_KEY", "")

        print("\nStarting Mutual Income Protection...")
        print(f"  Landing page:      {api_base}/")
        print(f"  Intake form:       {api_base}/apply")
        print(f"  Admin dashboard:   http://127.0.0.1:{streamlit_port}")
        print(f"  Agent NPN:         20476670")
        print("\nKeep this window open. Press Ctrl+C to stop.\n")

        api_proc = subprocess.Popen(
            [py, "-m", "uvicorn", "app.main:app", "--host", api_host, "--port", str(api_port)],
            cwd=ROOT,
            env=env_vars,
        )

        if not wait_for_api(api_base):
            raise RuntimeError("API failed to start. Check if another program is using the port.")

        streamlit_proc = subprocess.Popen(
            [
                py, "-m", "streamlit", "run", str(ROOT / "streamlit_app.py"),
                "--server.port", str(streamlit_port),
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false",
            ],
            cwd=ROOT,
            env=env_vars,
        )

        time.sleep(2)
        open_browsers(streamlit_port, api_base)
        api_proc.wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as exc:
        print(f"\nERROR: {exc}")
        pause_on_exit()
        raise SystemExit(1) from exc
    finally:
        if api_proc or streamlit_proc:
            stop_processes(*(p for p in (streamlit_proc, api_proc) if p is not None))


if __name__ == "__main__":
    main()