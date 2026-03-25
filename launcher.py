"""
웹문자보내기 - 실행 파일 진입점
PyInstaller exe 및 일반 Python 실행 모두 지원
pywebview로 독립 GUI 창 표시
"""

import sys
import os
import threading
import multiprocessing

# ── PyInstaller 멀티프로세싱 무한 생성 방지 ──
multiprocessing.freeze_support()

# ── windowed 모드에서 stdout/stderr가 None이면 devnull로 대체 ──
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# ── 경로 설정 ─────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

os.chdir(BASE_DIR)

# ── .env 로드 (exe/스크립트 모두) ─────────────────────────────
from dotenv import load_dotenv

env_path = os.path.join(EXE_DIR, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

# ── exe 실행 시 데이터 파일을 exe 옆에서 관리 ─────────────────
import contacts
import templates_store
from pathlib import Path

if getattr(sys, "frozen", False):
    contacts.CONTACTS_FILE = Path(EXE_DIR) / "contacts.json"
    templates_store.TEMPLATES_FILE = Path(EXE_DIR) / "templates.json"

# ── 사용 가능한 포트 찾기 ─────────────────────────────────────
import socket

def find_free_port(preferred=8321):
    """preferred 포트가 사용 가능하면 사용, 아니면 빈 포트 자동 할당"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", preferred))
        sock.close()
        return preferred
    except OSError:
        sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

PORT = find_free_port(8321)

# ── 서버 시작 (백그라운드 스레드) ─────────────────────────────
def _start_server():
    import uvicorn
    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=PORT,
        reload=False,
        log_level="warning",
    )


# ── 메인 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import webview

    # 서버를 백그라운드 데몬 스레드로 시작
    server_thread = threading.Thread(target=_start_server, daemon=True)
    server_thread.start()

    # pywebview 독립 창 생성
    window = webview.create_window(
        "웹문자보내기",
        url=f"http://127.0.0.1:{PORT}",
        width=480,
        height=860,
        resizable=True,
        min_size=(400, 600),
    )

    # GUI 이벤트 루프 시작 (창 닫으면 프로그램 종료)
    webview.start()
