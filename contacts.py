"""
연락처 저장/관리 모듈 (contacts.json 파일 기반)
"""

import json
from pathlib import Path
from datetime import datetime

CONTACTS_FILE = Path(__file__).parent / "contacts.json"


def _load() -> list:
    if not CONTACTS_FILE.exists():
        return []
    try:
        return json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(contacts: list):
    CONTACTS_FILE.write_text(
        json.dumps(contacts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_contacts() -> list:
    """최근 사용 순으로 정렬된 연락처 목록 반환"""
    contacts = _load()
    contacts.sort(key=lambda x: x.get("last_used", ""), reverse=True)
    return contacts


def upsert_contact(phone: str, name: str = "", memo: str = "") -> dict:
    """
    번호가 이미 있으면 last_used 갱신, 없으면 신규 추가.
    name/memo는 빈 문자열이면 기존 값 유지.
    """
    contacts = _load()
    now = datetime.now().isoformat(timespec="seconds")

    for c in contacts:
        if c["phone"] == phone:
            c["last_used"] = now
            if name:
                c["name"] = name
            if memo:
                c["memo"] = memo
            _save(contacts)
            return c

    new_id = max((c.get("id", 0) for c in contacts), default=0) + 1
    contact = {
        "id": new_id,
        "phone": phone,
        "name": name,
        "memo": memo,
        "last_used": now,
    }
    contacts.append(contact)
    _save(contacts)
    return contact


def update_contact(contact_id: int, name: str, memo: str) -> dict | None:
    """이름과 메모 수정"""
    contacts = _load()
    for c in contacts:
        if c.get("id") == contact_id:
            c["name"] = name
            c["memo"] = memo
            _save(contacts)
            return c
    return None


def delete_contact(contact_id: int) -> bool:
    """연락처 삭제"""
    contacts = _load()
    filtered = [c for c in contacts if c.get("id") != contact_id]
    if len(filtered) == len(contacts):
        return False
    _save(filtered)
    return True
