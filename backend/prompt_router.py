"""Prompt Router — 依任務類型載入對應的 Prompt Template

Phase 2 核心：Prompt 不寫死在程式裡，而是模組化存在 prompts/*.md。
本模組負責 Task → 選 Prompt → 組合最終 system prompt。

流程（配合 ai_router.classify_task）：
    使用者訊息
        ↓  ai_router.classify_task()  → task_type
        ↓  prompt_router.build_system_prompt(task_type, ...)
        ↓  讀 prompts/system.md（共用基底）+ prompts/<task>.md（任務專屬）
        ↓  疊加關係階段 / 角色 Soul / persona
        ↓  回傳最終 system prompt 字串

設計原則：
- Prompt 內容全部在 .md 檔，改 prompt 不用改程式。
- 檔案讀取有快取（避免每次請求都讀磁碟），可用 reload_prompts() 清除。
- 找不到對應 template 時 fallback 到 chat.md，再不行用最小內建字串。
"""

from __future__ import annotations

import os
from functools import lru_cache

from ai_router import ALL_TASKS, TASK_CHAT, TASK_ROLEPLAY

# prompts/ 目錄（與本檔同層）
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

SYSTEM_BASE_FILE = "system.md"

# 任務類型 → prompt 檔名對應（Task → Prompt Template）
TASK_PROMPT_FILE: dict[str, str] = {task: f"{task}.md" for task in ALL_TASKS}

# 最小內建 fallback（連 chat.md 都讀不到時才用，確保永不壞）
_HARDCODED_FALLBACK = (
    "你是 sexline 平台的 AI 助理，一律用繁體中文（台灣用語）回覆，"
    "精準、有條理、不捏造事實。"
)


def _read_prompt_file(filename: str) -> str | None:
    """讀取單一 prompt 檔，找不到回 None。"""
    path = os.path.join(PROMPTS_DIR, filename)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


@lru_cache(maxsize=64)
def _load_prompt_cached(filename: str) -> str | None:
    return _read_prompt_file(filename)


def reload_prompts() -> None:
    """清除 prompt 快取（改了 .md 檔後呼叫，或熱重載時用）。"""
    _load_prompt_cached.cache_clear()


def get_task_prompt(task_type: str) -> str:
    """取得某任務類型的 Prompt Template 內容（含 fallback 鏈）。"""
    filename = TASK_PROMPT_FILE.get(task_type, TASK_PROMPT_FILE[TASK_CHAT])
    content = _load_prompt_cached(filename)
    if content:
        return content
    # fallback 1：chat.md
    chat_content = _load_prompt_cached(TASK_PROMPT_FILE[TASK_CHAT])
    if chat_content:
        return chat_content
    # fallback 2：硬編字串
    return _HARDCODED_FALLBACK


def get_system_base() -> str:
    """取得共用系統基底（system.md）。"""
    return _load_prompt_cached(SYSTEM_BASE_FILE) or ""


def list_available_prompts() -> dict[str, bool]:
    """回傳每個任務類型的 template 是否存在（供 /prompts 端點 / 測試用）。"""
    status = {}
    for task, filename in TASK_PROMPT_FILE.items():
        status[task] = os.path.isfile(os.path.join(PROMPTS_DIR, filename))
    status[f"_base:{SYSTEM_BASE_FILE}"] = os.path.isfile(
        os.path.join(PROMPTS_DIR, SYSTEM_BASE_FILE)
    )
    return status


def build_system_prompt(
    task_type: str,
    *,
    stage_prompt: str | None = None,
    soul_block: str | None = None,
    persona_block: str | None = None,
) -> str:
    """組合最終 system prompt。

    層次（由上到下疊加）：
        1. system.md          共用基底
        2. <task>.md          任務專屬 template
        3. soul_block         角色靈魂設定（roleplay 時由 main 傳入）
        4. stage_prompt       關係階段指令（roleplay 時）
        5. persona_block      使用者自訂 persona（可選）

    非角色扮演任務（coding/debug/...）通常只用 1+2，
    stage/soul/persona 為 None 時自動略過。
    """
    parts: list[str] = []

    base = get_system_base()
    if base:
        parts.append(base)

    task_prompt = get_task_prompt(task_type)
    parts.append(f"[當前任務：{task_type}]\n{task_prompt}")

    # 角色扮演專屬層次：soul + 關係階段（其他任務不注入，避免污染程式/分析任務）
    if task_type == TASK_ROLEPLAY:
        if soul_block:
            parts.append(f"[角色設定]\n{soul_block}")
        if stage_prompt:
            parts.append(f"[關係階段]\n{stage_prompt}")

    # persona 是使用者自訂人格，任何任務都注入（若有提供）
    if persona_block:
        parts.append(f"[使用者自訂人格]\n{persona_block}")

    return "\n\n".join(p for p in parts if p).strip()
