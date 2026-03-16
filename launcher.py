"""
웹문자보내기 - 실행 파일 진입점
PyInstaller exe 및 일반 Python 실행 모두 지원
pywebview로 독립 GUI 창 표시
"""

import sys
import os
import threading

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

# ── exe 실행 시 .env와 contacts.json을 exe 옆에서 관리 ────────
if getattr(sys, "frozen", False):
    from dotenv import load_dotenv
    env_path = os.path.join(EXE_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)

    import contacts
    from pathlib import Path
    contacts.CONTACTS_FILE = Path(EXE_DIR) / "contacts.json"


# ── 서버 시작 (백그라운드 스레드) ─────────────────────────────
def _start_server():
    import uvicorn
    from main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
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
        url="http://127.0.0.1:8000",
        width=520,
        height=820,
        resizable=True,
        min_size=(400, 600),
    )

    # GUI 이벤트 루프 시작 (창 닫으면 프로그램 종료)
    webview.start()
