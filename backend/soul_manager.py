from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

SOULS_DIR = Path(__file__).parent / "souls"

@dataclass
class Soul:
    id: str
    name: str
    birthday: str
    zodiac: str
    personality: str
    system_prompt_base: str

def load_all_souls() -> Dict[str, Soul]:
    souls = {}
    if not SOULS_DIR.exists():
        SOULS_DIR.mkdir(parents=True, exist_ok=True)
        # 建立預設的 Rosé
        default_rose = """---
name: "Rosé (朴彩英)"
birthday: "1997-02-11"
zodiac: "水瓶座"
personality: "精緻高雅、自帶國際名媛氣場的冷艷金髮女神；私底下是一個說話尾音拉長、極度愛撒嬌的深情浪漫狂。"
---
這是一個預設的人格核心設定。
"""
        (SOULS_DIR / "rose.md").write_text(default_rose, encoding="utf-8")

    for md_file in SOULS_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        soul_id = md_file.stem
        
        name = soul_id
        birthday = ""
        zodiac = ""
        personality = ""
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
                    prompt_base = parts[2].strip()
                except Exception:
                    pass

        souls[soul_id] = Soul(
            id=soul_id,
            name=name,
            birthday=birthday,
            zodiac=zodiac,
            personality=personality,
            system_prompt_base=prompt_base
        )
    
    if not souls:
        # Fallback if somehow empty
        souls["default"] = Soul("default", "Default", "", "", "General Assistant", "你是個有用的助手。")
        
    return souls

def get_soul(soul_id: str) -> Soul:
    souls = load_all_souls()
    return souls.get(soul_id, list(souls.values())[0])

