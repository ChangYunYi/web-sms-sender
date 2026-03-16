"""
웹문자보내기 - 실행 파일 진입점
PyInstaller exe 및 일반 Python 실행 모두 지원
"""

import sys
import os
import threading
import webbrowser
import time

# ── windowed 모드에서 stdout/stderr가 None이면 devnull로 대체 ──
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# ── 경로 설정 ─────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # PyInstaller exe: 번들 리소스 경로
    BASE_DIR = sys._MEIPASS
    # exe가 위치한 디렉터리 (사용자 데이터 저장용)
    EXE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXE_DIR = BASE_DIR

# templates/, static/ 상대 경로가 동작하도록 작업 디렉터리 설정
os.chdir(BASE_DIR)

# ── exe 실행 시 .env와 contacts.json을 exe 옆에서 관리 ────────
if getattr(sys, "frozen", False):
    # .env를 exe 디렉터리에서 로드
    from dotenv import load_dotenv
    env_path = os.path.join(EXE_DIR, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)

    # contacts.json을 exe 디렉터리에 저장하도록 경로 변경
    import contacts
    from pathlib import Path
    contacts.CONTACTS_FILE = Path(EXE_DIR) / "contacts.json"


# ── 브라우저 자동 열기 ────────────────────────────────────────
def _open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")


# ── 서버 시작 ─────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    from main import app

    print("웹문자보내기 서버를 시작합니다...")
    print("브라우저에서 http://localhost:8000 으로 접속하세요.")
    print("종료하려면 이 창을 닫으세요.\n")

    threading.Thread(target=_open_browser, daemon=True).start()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
