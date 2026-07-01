"""AI Router — 智慧模型路由

使用者不需要自己選模型。AI 依訊息內容自動判斷任務類型，
再挑選「最適合且目前可用」的模型。

路由表（理想對應）：
    chat / roleplay / translate  → 本地模型 (Qwen)     便宜、快、隱私
    python / debug               → DeepSeek            程式強、便宜
    react / vite / ui            → Claude              前端與 UI 最佳
    analysis (大型分析)          → GPT                 長上下文、推理
    code_review                  → Claude 或 GPT       擇一可用
    docs (文件)                  → GPT                 條理、長文

實際挑選時會 fallback 到目前 available 的模型，
確保就算某 provider 沒設 key 也不會壞。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---- 任務類型 ----------------------------------------------------------------

TASK_CHAT = "chat"
TASK_ROLEPLAY = "roleplay"
TASK_TRANSLATE = "translate"
TASK_PYTHON = "python"
TASK_DEBUG = "debug"
TASK_UI = "ui"
TASK_ANALYSIS = "analysis"
TASK_CODE_REVIEW = "code_review"
TASK_DOCS = "docs"

# 每個任務類型偏好的 provider 順序（第一個可用者勝出）
TASK_PROVIDER_PREFERENCE: dict[str, list[str]] = {
    TASK_CHAT:        ["local", "openrouter", "deepseek", "gemini"],
    TASK_ROLEPLAY:    ["local", "openrouter", "gemini", "deepseek"],
    TASK_TRANSLATE:   ["local", "deepseek", "openrouter", "gemini"],
    TASK_PYTHON:      ["deepseek", "openrouter", "openai-api", "local"],
    TASK_DEBUG:       ["deepseek", "openrouter", "openai-api", "local"],
    TASK_UI:          ["openrouter", "openai-api", "deepseek", "local"],   # Claude 走 openrouter
    TASK_ANALYSIS:    ["openai-api", "openrouter", "gemini", "deepseek"],  # GPT
    TASK_CODE_REVIEW: ["openrouter", "openai-api", "deepseek", "local"],   # Claude / GPT
    TASK_DOCS:        ["openai-api", "openrouter", "gemini", "deepseek"],  # GPT
}

# 針對特定 provider，偏好的模型關鍵字（用來從清單挑「最像」的那顆）
TASK_MODEL_HINT: dict[str, list[str]] = {
    TASK_UI:          ["claude", "sonnet"],
    TASK_CODE_REVIEW: ["claude", "sonnet", "gpt-4", "gpt-5", "o1", "o3"],
    TASK_ANALYSIS:    ["gpt-5", "gpt-4", "o1", "o3", "claude", "opus"],
    TASK_DOCS:        ["gpt-4", "gpt-5", "claude"],
    TASK_PYTHON:      ["deepseek", "coder", "claude"],
    TASK_DEBUG:       ["deepseek", "coder", "claude"],
    TASK_CHAT:        ["qwen", "haiku", "flash", "chat"],
    TASK_ROLEPLAY:    ["qwen", "haiku", "opus", "flash"],
    TASK_TRANSLATE:   ["qwen", "deepseek", "flash"],
}


# ---- 關鍵字偵測 --------------------------------------------------------------

_TRANSLATE_KW = re.compile(
    r"(翻譯|translate|翻成|譯成|中翻英|英翻中|日翻|翻中|翻英|譯為)", re.I
)
_DEBUG_KW = re.compile(
    r"(debug|除錯|報錯|error|traceback|exception|bug|修不好|壞掉|不能跑|"
    r"stack ?trace|為什麼.*(錯|失敗)|fix.*error)", re.I
)
_UI_KW = re.compile(
    r"(react|vite|vue|svelte|tailwind|css|前端|ui|介面|樣式|component|"
    r"元件|按鈕|排版|rwd|響應式|畫面|layout|jsx|tsx)", re.I
)
_PYTHON_KW = re.compile(
    r"(python|\.py\b|pandas|numpy|fastapi|django|flask|pytest|"
    r"寫.*(腳本|script)|def |import |pip install)", re.I
)
_REVIEW_KW = re.compile(
    r"(code ?review|審核.*(程式|代碼|code)|review.*(pr|code)|檢查.*(程式|代碼)|"
    r"重構|refactor|優化.*(程式|代碼))", re.I
)
_DOCS_KW = re.compile(
    r"(寫.*(文件|文檔|readme|說明|教學|規格書|報告)|documentation|"
    r"生成.*文件|整理成.*文件|寫一份)", re.I
)
_ANALYSIS_KW = re.compile(
    r"(分析|analyze|評估|比較|架構|architecture|策略|規劃|方案|"
    r"深入.*(探討|研究)|長篇|整體.*(檢視|盤點))", re.I
)
_CODE_HINT = re.compile(r"(```|def |class |function |const |let |=>|</|/>|SELECT |import )")

# 角色扮演 / 親密關係訊號（sexline 主要用途）
_ROLEPLAY_KW = re.compile(
    r"(抱抱|親親|想你|愛你|寶貝|老公|老婆|撒嬌|摸摸|拍拍肩|\(|（|嗯+~|哦+~)", re.I
)


@dataclass
class RouteDecision:
    task_type: str
    reason: str


def classify_task(message: str) -> RouteDecision:
    """依訊息內容判斷任務類型。順序即優先級（越專門越先判）。"""
    msg = message or ""

    # 1. 翻譯（很明確的意圖）
    if _TRANSLATE_KW.search(msg):
        return RouteDecision(TASK_TRANSLATE, "偵測到翻譯意圖")

    # 2. Code Review / 重構
    if _REVIEW_KW.search(msg):
        return RouteDecision(TASK_CODE_REVIEW, "偵測到 code review / 重構意圖")

    # 3. Debug / 報錯
    if _DEBUG_KW.search(msg):
        return RouteDecision(TASK_DEBUG, "偵測到除錯 / 報錯關鍵字")

    # 4. UI / 前端
    if _UI_KW.search(msg):
        return RouteDecision(TASK_UI, "偵測到前端 / UI 關鍵字")

    # 5. Python / 程式
    if _PYTHON_KW.search(msg):
        return RouteDecision(TASK_PYTHON, "偵測到 Python / 程式關鍵字")

    # 6. 文件
    if _DOCS_KW.search(msg):
        return RouteDecision(TASK_DOCS, "偵測到文件撰寫意圖")

    # 7. 大型分析（含程式碼片段但非上述明確類型時，長訊息傾向分析）
    if _ANALYSIS_KW.search(msg) or (_CODE_HINT.search(msg) and len(msg) > 400):
        return RouteDecision(TASK_ANALYSIS, "偵測到分析 / 架構意圖或長篇內容")

    # 8. 角色扮演（sexline 核心）
    if _ROLEPLAY_KW.search(msg):
        return RouteDecision(TASK_ROLEPLAY, "偵測到角色扮演 / 親密互動訊號")

    # 9. 預設：一般聊天
    return RouteDecision(TASK_CHAT, "一般聊天（預設）")


def _score_model(choice, hints: list[str]) -> int:
    """依 hint 關鍵字對模型評分，越高越符合。"""
    text = f"{choice.model} {choice.label}".lower()
    score = 0
    for i, kw in enumerate(hints):
        if kw.lower() in text:
            # 越前面的 hint 權重越高
            score += (len(hints) - i) * 10
    return score


def route_model(message: str, choices: list, current_choice=None):
    """核心路由：回傳 (選中的 ModelChoice, RouteDecision)。

    choices: get_model_choices() 的結果。
    current_choice: 找不到任何可用模型時的 fallback（通常是當前模型）。
    """
    decision = classify_task(message)

    available = [c for c in choices if c.is_available()]
    if not available:
        return current_choice or (choices[0] if choices else None), decision

    provider_pref = TASK_PROVIDER_PREFERENCE.get(decision.task_type, ["local"])
    hints = TASK_MODEL_HINT.get(decision.task_type, [])

    # 依 provider 偏好順序找第一個有可用模型的 provider，
    # 在該 provider 內用 hint 挑最符合的模型。
    for provider in provider_pref:
        candidates = [c for c in available if c.provider == provider]
        if not candidates:
            continue
        if hints:
            candidates = sorted(
                candidates, key=lambda c: _score_model(c, hints), reverse=True
            )
        return candidates[0], decision

    # 所有偏好 provider 都沒有 → 用第一個可用模型
    return available[0], decision
