"""
멘트(템플릿) 저장/관리 모듈 (templates.json 파일 기반)
"""

import json
from pathlib import Path
from datetime import datetime

TEMPLATES_FILE = Path(__file__).parent / "templates.json"


def _load() -> list:
    if not TEMPLATES_FILE.exists():
        return []
    try:
        return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(templates: list):
    TEMPLATES_FILE.write_text(
        json.dumps(templates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_templates() -> list:
    """저장된 멘트 목록 반환 (최신순)"""
    return _load()


def add_template(title: str, content: str) -> dict:
    """새 멘트 추가"""
    templates = _load()
    new_id = max((t.get("id", 0) for t in templates), default=0) + 1
    template = {
        "id": new_id,
        "title": title,
        "content": content,
        "created": datetime.now().isoformat(timespec="seconds"),
    }
    templates.insert(0, template)
    _save(templates)
    return template


def delete_template(template_id: int) -> bool:
    """멘트 삭제"""
    templates = _load()
    filtered = [t for t in templates if t.get("id") != template_id]
    if len(filtered) == len(templates):
        return False
    _save(filtered)
    return True
