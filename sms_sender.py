"""
네이버 클라우드 SENS API를 이용한 SMS 발송 모듈
"""

import hmac
import hashlib
import base64
import time
import os
import json as json_lib

import httpx
from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("NCP_ACCESS_KEY", "")
SECRET_KEY = os.getenv("NCP_SECRET_KEY", "")
SERVICE_ID = os.getenv("NCP_SERVICE_ID", "")
SENDER = os.getenv("NCP_SENDER", "")

BASE_URL = "https://sens.apigw.ntruss.com"


def is_configured() -> bool:
    """모든 API 설정값이 입력되었는지 확인 (ASCII 문자만 유효)"""
    values = [ACCESS_KEY, SECRET_KEY, SERVICE_ID, SENDER]
    return all(values) and all(v.isascii() for v in values)


def _make_signature(timestamp: str) -> str:
    """SENS API 인증용 HMAC-SHA256 서명 생성"""
    uri = f"/sms/v2/services/{SERVICE_ID}/messages"
    message = f"POST {uri}\n{timestamp}\n{ACCESS_KEY}"
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(signature).decode("utf-8")


async def send_sms(phone: str, message: str) -> dict:
    """
    SENS API로 SMS 발송
    phone:   수신자 번호 (예: 01012345678)
    message: 메시지 내용 (80자 이하 단문 / 초과 시 장문)
    """
    phone_clean = "".join(filter(str.isdigit, phone))
    if not phone_clean:
        return {"success": False, "error": "올바른 전화번호를 입력해주세요."}

    if not is_configured():
        return {
            "success": False,
            "error": ".env 파일에 API 설정이 누락되었습니다. 설정 안내를 확인해주세요.",
        }

    timestamp = str(int(time.time() * 1000))
    uri = f"/sms/v2/services/{SERVICE_ID}/messages"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": ACCESS_KEY,
        "x-ncp-apigw-signature-v2": _make_signature(timestamp),
    }

    # 80자 초과 시 자동으로 LMS(장문)로 전환
    sms_type = "SMS" if len(message) <= 80 else "LMS"

    body = {
        "type": sms_type,
        "from": SENDER,
        "content": message,
        "messages": [{"to": phone_clean}],
    }

    try:
        body_bytes = json_lib.dumps(body, ensure_ascii=False).encode("utf-8")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}{uri}",
                headers=headers,
                content=body_bytes,
                timeout=15.0,
            )

        if resp.status_code == 202:
            return {"success": True, "message": f"{phone_clean}으로 문자 전송 완료!"}

        # 오류 응답 파싱
        try:
            data = resp.json()
            err_msg = data.get("error", {}).get("message", str(data))
        except Exception:
            err_msg = resp.text

        return {"success": False, "error": f"API 오류 ({resp.status_code}): {err_msg}"}

    except httpx.TimeoutException:
        return {"success": False, "error": "요청 시간 초과. 네트워크 상태를 확인해주세요."}
    except Exception as e:
        return {"success": False, "error": f"전송 실패: {str(e)}"}
