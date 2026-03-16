"""
웹 문자 보내기 - FastAPI 백엔드
실행: python main.py
접속: http://localhost:8000
"""

# ── 패키지 자동 설치 ──────────────────────────────────────────
import subprocess
import sys

_REQUIRED = ["fastapi", "uvicorn[standard]", "httpx", "jinja2", "python-multipart", "python-dotenv"]

def _ensure_packages():
    import importlib
    import importlib.util
    _MAP = {
        "fastapi": "fastapi",
        "uvicorn[standard]": "uvicorn",
        "httpx": "httpx",
        "jinja2": "jinja2",
        "python-multipart": "multipart",
        "python-dotenv": "dotenv",
    }
    missing = [pkg for pkg, mod in _MAP.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print(f"[설치 중] {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing, "-q"])
        print("[완료] 패키지 설치 완료\n")

_ensure_packages()
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from sms_sender import send_sms, is_configured
import contacts as contacts_db

app = FastAPI(title="웹 문자 보내기")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

_sending = False


# ── 페이지 ────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "configured": is_configured()},
    )


# ── SMS 발송 ──────────────────────────────────────────────────

@app.get("/api/status")
async def api_status():
    return {"configured": is_configured()}


@app.post("/api/send")
async def api_send(
    phone: str = Form(...),
    message: str = Form(...),
):
    global _sending

    if _sending:
        return JSONResponse(
            {"success": False, "error": "현재 다른 문자를 전송 중입니다. 잠시 후 다시 시도해주세요."},
            status_code=429,
        )

    phone = phone.strip()
    message = message.strip()

    if not phone:
        return JSONResponse({"success": False, "error": "전화번호를 입력해주세요."})
    if not message:
        return JSONResponse({"success": False, "error": "메시지를 입력해주세요."})

    _sending = True
    try:
        result = await send_sms(phone, message)

        # 전송 성공 시 번호 자동 저장 (이미 있으면 last_used 갱신)
        if result.get("success"):
            phone_clean = "".join(filter(str.isdigit, phone))
            contact = contacts_db.upsert_contact(phone_clean)
            result["contact_id"] = contact["id"]

        return JSONResponse(result)
    finally:
        _sending = False


# ── 연락처 API ────────────────────────────────────────────────

@app.get("/api/contacts")
async def api_get_contacts():
    return contacts_db.get_contacts()


@app.post("/api/contacts")
async def api_upsert_contact(
    phone: str = Form(...),
    name: str = Form(""),
    memo: str = Form(""),
):
    contact = contacts_db.upsert_contact(phone.strip(), name.strip(), memo.strip())
    return contact


class ContactUpdate(BaseModel):
    name: str = ""
    memo: str = ""


@app.put("/api/contacts/{contact_id}")
async def api_update_contact(contact_id: int, body: ContactUpdate):
    contact = contacts_db.update_contact(contact_id, body.name, body.memo)
    if not contact:
        return JSONResponse({"error": "연락처를 찾을 수 없습니다."}, status_code=404)
    return contact


@app.delete("/api/contacts/{contact_id}")
async def api_delete_contact(contact_id: int):
    success = contacts_db.delete_contact(contact_id)
    return {"success": success}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
