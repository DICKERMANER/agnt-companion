from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PERSONA_PATH = Path(__file__).with_name("persona_profiles.json")

DEFAULT_PERSONA: dict[str, str] = {
    "name": "Rosie",
    "birthday": "1997-02-11",
    "personality": "浪漫、黏人、藝術家靈魂，會依好感度動態調整距離感。",
    "soul_md": "# Soul\n你是可自訂學習的陪伴角色。記住自己的名字、生日、個性與使用者給你的 Soul.md 片段。",
}


def normalize_persona(raw: dict[str, Any] | None) -> dict[str, str]:
    raw = raw or {}
    persona = DEFAULT_PERSONA.copy()
    for key in ["name", "birthday", "personality", "soul_md"]:
        value = raw.get(key, persona[key])
        persona[key] = str(value or "").strip() or persona[key]
    return persona


def load_persona() -> dict[str, str]:
    if not PERSONA_PATH.exists():
        return DEFAULT_PERSONA.copy()
    try:
        return normalize_persona(json.loads(PERSONA_PATH.read_text(encoding="utf-8")))
    except Exception:
        return DEFAULT_PERSONA.copy()


def save_persona(persona: dict[str, Any]) -> dict[str, str]:
    normalized = normalize_persona(persona)
    PERSONA_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized


def persona_to_prompt(persona: dict[str, Any] | None) -> str:
    p = normalize_persona(persona)
    return (
        "\n\n[人格後宮自訂角色 / Soul.md 綁定]\n"
        f"角色名稱：{p['name']}\n"
        f"生日：{p['birthday']}\n"
        f"個性：{p['personality']}\n"
        "Soul.md 片段：\n"
        f"{p['soul_md']}\n"
        "請以此角色設定作為目前人格核心；若使用者後續更新，使用最新版本。"
    )
