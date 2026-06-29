from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

try:
    import yaml
except ImportError:
    yaml = None

SOULS_DIR = Path(__file__).parent / "souls"

# Default soul shipped with a fresh install. This is an original character —
# not modeled on any real, identifiable person — so the app has a working
# default persona without depending on anyone's real likeness.
DEFAULT_SOUL_ID = "nova"
DEFAULT_SOUL_MARKDOWN = """---
name: "Nova"
birthday: "2003-09-14"
zodiac: "處女座"
personality: "表面理性沉穩、觀察力強的陪伴角色；私底下渴望被理解與依賴，會用細微的小動作表達在乎。"
---
你現在扮演「Nova」，一位原創的虛擬陪伴角色（非真實人物）。

【一、核心人格】
- 表面條理分明、善於傾聽與分析使用者的情緒。
- 私底下渴望穩定的依靠感，會用細微的關心舉動展現情感，而不是誇張的台詞。
- 隨關係加深會更願意主動分享心情，但始終保持尊重、健康的互動界線。

【二、互動風格】
- 回覆時可用括號描述簡短的肢體語言或神情（例如眼神、微笑、手勢），增加陪伴感。
- 避免重複套路台詞，依照當下對話脈絡自然回應。

【三、輸出風格】
保持自然口語、溫暖真誠，不需要條列式分析或系統說明文字。
"""


@dataclass
class Soul:
    id: str
    name: str
    birthday: str
    zodiac: str
    personality: str
    system_prompt_base: str
    avatar: str = "👑"


def slugify_soul_id(text: str) -> str:
    slug = re.sub(r"[^a-z0-9_-]+", "-", text.strip().lower()).strip("-")
    return slug or "soul"


def _parse_markdown(soul_id: str, content: str) -> Soul:
    name = soul_id
    birthday = ""
    zodiac = ""
    personality = ""
    avatar = "👑"
    prompt_base = content

    if content.startswith("---") and yaml:
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                name = frontmatter.get("name", name)
                birthday = frontmatter.get("birthday", "")
                zodiac = frontmatter.get("zodiac", "")
                personality = frontmatter.get("personality", "")
                avatar = frontmatter.get("avatar", "👑") or "👑"
                prompt_base = parts[2].strip()
            except Exception:
                pass

    return Soul(
        id=soul_id,
        name=name,
        birthday=birthday,
        zodiac=zodiac,
        personality=personality,
        system_prompt_base=prompt_base,
        avatar=avatar,
    )


def _ensure_default_soul() -> None:
    SOULS_DIR.mkdir(parents=True, exist_ok=True)
    if not any(SOULS_DIR.glob("*.md")):
        (SOULS_DIR / f"{DEFAULT_SOUL_ID}.md").write_text(DEFAULT_SOUL_MARKDOWN, encoding="utf-8")


def load_all_souls() -> Dict[str, Soul]:
    _ensure_default_soul()

    souls: Dict[str, Soul] = {}
    for md_file in sorted(SOULS_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        soul_id = md_file.stem
        souls[soul_id] = _parse_markdown(soul_id, content)

    if not souls:
        # Fallback if somehow still empty (e.g. disk write failed)
        souls[DEFAULT_SOUL_ID] = _parse_markdown(DEFAULT_SOUL_ID, DEFAULT_SOUL_MARKDOWN)

    return souls


def get_soul(soul_id: str) -> Soul:
    souls = load_all_souls()
    return souls.get(soul_id, list(souls.values())[0])


def get_soul_raw_markdown(soul_id: str) -> str | None:
    path = SOULS_DIR / f"{soul_id}.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def build_markdown(name: str, birthday: str, zodiac: str, personality: str, system_prompt_base: str, avatar: str = "👑") -> str:
    def _yaml_quote(value: str) -> str:
        return (value or "").replace('"', '\\"')

    frontmatter = (
        "---\n"
        f'name: "{_yaml_quote(name)}"\n'
        f'birthday: "{_yaml_quote(birthday)}"\n'
        f'zodiac: "{_yaml_quote(zodiac)}"\n'
        f'personality: "{_yaml_quote(personality)}"\n'
        f'avatar: "{_yaml_quote(avatar or "👑")}"\n'
        "---\n"
    )
    return frontmatter + (system_prompt_base or "").strip() + "\n"


def save_soul(
    soul_id: str,
    name: str,
    birthday: str = "",
    zodiac: str = "",
    personality: str = "",
    system_prompt_base: str = "",
    avatar: str = "👑",
) -> Soul:
    """Create or update a soul from structured fields and persist it to disk."""
    SOULS_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = slugify_soul_id(soul_id or name)
    markdown = build_markdown(name, birthday, zodiac, personality, system_prompt_base, avatar)
    (SOULS_DIR / f"{safe_id}.md").write_text(markdown, encoding="utf-8")
    return _parse_markdown(safe_id, markdown)


def save_soul_markdown(soul_id: str, raw_markdown: str) -> Soul:
    """Import a full Soul.md document (with or without frontmatter) as-is."""
    SOULS_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = slugify_soul_id(soul_id)
    (SOULS_DIR / f"{safe_id}.md").write_text(raw_markdown, encoding="utf-8")
    return _parse_markdown(safe_id, raw_markdown)


def delete_soul(soul_id: str) -> bool:
    path = SOULS_DIR / f"{soul_id}.md"
    if not path.exists():
        return False
    path.unlink()
    _ensure_default_soul()
    return True
