"""AI Router — 智慧模型路由 + 任務分類

使用者不需要自己選模型。AI 依訊息內容自動判斷任務類型，
再挑選「最適合且目前可用」的模型。

任務分類（classify_task）同時被 prompt_router.py 使用來挑選 Prompt template，
所以這裡是「任務類型」的單一真實來源（Single Source of Truth）。

路由表（理想對應）：
    chat / roleplay / translate  → 本地模型 (Qwen)     便宜、快、隱私
    python / debug / coding      → DeepSeek            程式強、便宜
    react / ui                   → Claude              前端與 UI 最佳
    architecture / review        → Claude 或 GPT       長上下文、推理
    financial / planning         → GPT                 推理、條理
    summary / search             → 便宜快速模型
實際挑選時會 fallback 到目前 available 的模型，
確保就算某 provider 沒設 key 也不會壞。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---- 任務類型（13 種，對應 prompts/*.md）--------------------------------------

TASK_CHAT = "chat"
TASK_CODING = "coding"
TASK_DEBUG = "debug"
TASK_PYTHON = "python"
TASK_REACT = "react"
TASK_UI = "ui"
TASK_ARCHITECTURE = "architecture"
TASK_REVIEW = "review"
TASK_FINANCIAL = "financial"
TASK_TRANSLATE = "translate"
TASK_SUMMARY = "summary"
TASK_ROLEPLAY = "roleplay"
TASK_SEARCH = "search"
TASK_PLANNING = "planning"

# 所有合法任務類型（供 prompt_router / 測試使用）
ALL_TASKS = [
    TASK_CHAT, TASK_CODING, TASK_DEBUG, TASK_PYTHON, TASK_REACT, TASK_UI,
    TASK_ARCHITECTURE, TASK_REVIEW, TASK_FINANCIAL, TASK_TRANSLATE,
    TASK_SUMMARY, TASK_ROLEPLAY, TASK_SEARCH, TASK_PLANNING,
]

# 每個任務類型偏好的 provider 順序（第一個可用者勝出）
TASK_PROVIDER_PREFERENCE: dict[str, list[str]] = {
    TASK_CHAT:         ["local", "openrouter", "deepseek", "gemini"],
    TASK_ROLEPLAY:     ["local", "openrouter", "gemini", "deepseek"],
    TASK_TRANSLATE:    ["local", "deepseek", "openrouter", "gemini"],
    TASK_SUMMARY:      ["local", "deepseek", "openrouter", "gemini"],
    TASK_SEARCH:       ["openrouter", "gemini", "deepseek", "local"],
    TASK_PYTHON:       ["deepseek", "openrouter", "openai-api", "local"],
    TASK_CODING:       ["deepseek", "openrouter", "openai-api", "local"],
    TASK_DEBUG:        ["deepseek", "openrouter", "openai-api", "local"],
    TASK_REACT:        ["openrouter", "openai-api", "deepseek", "local"],   # Claude 走 openrouter
    TASK_UI:           ["openrouter", "openai-api", "deepseek", "local"],   # Claude 走 openrouter
    TASK_ARCHITECTURE: ["openai-api", "openrouter", "gemini", "deepseek"],  # GPT / Claude
    TASK_REVIEW:       ["openrouter", "openai-api", "deepseek", "local"],   # Claude / GPT
    TASK_FINANCIAL:    ["openai-api", "openrouter", "gemini", "deepseek"],  # GPT
    TASK_PLANNING:     ["openai-api", "openrouter", "gemini", "deepseek"],  # GPT
}

# 針對特定 provider，偏好的模型關鍵字（用來從清單挑「最像」的那顆）
TASK_MODEL_HINT: dict[str, list[str]] = {
    TASK_REACT:        ["claude", "sonnet"],
    TASK_UI:           ["claude", "sonnet"],
    TASK_REVIEW:       ["claude", "sonnet", "gpt-4", "gpt-5", "o1", "o3"],
    TASK_ARCHITECTURE: ["gpt-5", "gpt-4", "o1", "o3", "claude", "opus"],
    TASK_FINANCIAL:    ["gpt-5", "gpt-4", "o1", "o3", "claude", "opus"],
    TASK_PLANNING:     ["gpt-4", "gpt-5", "claude", "opus"],
    TASK_PYTHON:       ["deepseek", "coder", "claude"],
    TASK_CODING:       ["deepseek", "coder", "claude", "sonnet"],
    TASK_DEBUG:        ["deepseek", "coder", "claude"],
    TASK_CHAT:         ["qwen", "haiku", "flash", "chat"],
    TASK_ROLEPLAY:     ["qwen", "haiku", "opus", "flash"],
    TASK_TRANSLATE:    ["qwen", "deepseek", "flash"],
    TASK_SUMMARY:      ["qwen", "haiku", "flash"],
    TASK_SEARCH:       ["gpt-4", "flash", "claude", "qwen"],
}


# ---- 關鍵字偵測 --------------------------------------------------------------

_TRANSLATE_KW = re.compile(
    r"(翻譯|translate|翻成|譯成|中翻英|英翻中|日翻|翻中|翻英|譯為)", re.I
)
_REVIEW_KW = re.compile(
    r"(code ?review|審核.*(程式|代碼|code)|review.*(pr|code)|檢查.*(程式|代碼)|"
    r"重構|refactor|優化.*(程式|代碼)|幫我看.*(程式|代碼))", re.I
)
_DEBUG_KW = re.compile(
    r"(debug|除錯|報錯|error|traceback|exception|bug|修不好|壞掉|不能跑|"
    r"stack ?trace|為什麼.*(錯|失敗)|fix.*error|噴錯|跑不動)", re.I
)
_REACT_KW = re.compile(
    r"(react|vite|vue|svelte|next\.?js|jsx|tsx|hook|useState|useEffect|component|元件)", re.I
)
_UI_KW = re.compile(
    r"(tailwind|css|前端樣式|ui|ux|介面|樣式|排版|rwd|響應式|畫面|layout|"
    r"配色|色碼|按鈕樣式|設計.*(介面|畫面|頁面))", re.I
)
_PYTHON_KW = re.compile(
    r"(python|\.py\b|pandas|numpy|fastapi|django|flask|pytest|"
    r"寫.*(腳本|script)|def |import |pip install)", re.I
)
_CODING_KW = re.compile(
    r"(寫.*(程式|函式|function|code|一個.*程式)|實作|實現|coding|"
    r"幫我.*(寫|做).*(程式|功能|api)|演算法|algorithm|leetcode)", re.I
)
_FINANCIAL_KW = re.compile(
    r"(股票|台股|美股|投資|財報|營收|殖利率|ETF|大盤|股價|漲跌|"
    r"財經|市場|供應鏈|標的|買進|賣出|停損|停利|財務|估值|本益比|"
    r"stock|invest|market|finance|portfolio)", re.I
)
_SUMMARY_KW = re.compile(
    r"(摘要|總結|重點整理|濃縮|懶人包|tl;?dr|summari[sz]e|"
    r"幫我.*(整理|濃縮).*重點|一句話.*(說|講|總結)|精簡成)", re.I
)
_PLANNING_KW = re.compile(
    r"(規劃|計畫|計劃|路線圖|roadmap|排程|時程|拆解.*(任務|步驟)|"
    r"專案.*(規劃|安排)|行動方案|plan|待辦|todo.*規劃|里程碑|milestone)", re.I
)
_ARCHITECTURE_KW = re.compile(
    r"(架構|architecture|系統設計|technical design|技術選型|方案評估|"
    r"microservice|微服務|scalab|擴展性|設計.*(系統|架構)|架構圖)", re.I
)
_SEARCH_KW = re.compile(
    r"(查一下|查詢|搜尋|search|找.*(資料|答案|資訊)|是什麼|怎麼用|"
    r"如何.*(安裝|設定|使用)|哪裡.*(下載|找)|what is|how to|文件在哪)", re.I
)
_ANALYSIS_KW = re.compile(
    r"(分析|analyze|評估|比較|策略|深入.*(探討|研究)|長篇|整體.*(檢視|盤點))", re.I
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

    # 1. 翻譯（意圖最明確）
    if _TRANSLATE_KW.search(msg):
        return RouteDecision(TASK_TRANSLATE, "偵測到翻譯意圖")

    # 2. Code Review / 重構
    if _REVIEW_KW.search(msg):
        return RouteDecision(TASK_REVIEW, "偵測到 code review / 重構意圖")

    # 3. Debug / 報錯
    if _DEBUG_KW.search(msg):
        return RouteDecision(TASK_DEBUG, "偵測到除錯 / 報錯關鍵字")

    # 4. 財經（sexline 內建投資助手，優先於一般 coding）
    if _FINANCIAL_KW.search(msg):
        return RouteDecision(TASK_FINANCIAL, "偵測到財經 / 投資關鍵字")

    # 5. React / 前端框架
    if _REACT_KW.search(msg):
        return RouteDecision(TASK_REACT, "偵測到 React / 前端框架關鍵字")

    # 6. UI 設計
    if _UI_KW.search(msg):
        return RouteDecision(TASK_UI, "偵測到 UI / 樣式設計關鍵字")

    # 7. Python
    if _PYTHON_KW.search(msg):
        return RouteDecision(TASK_PYTHON, "偵測到 Python 關鍵字")

    # 8. 一般程式撰寫
    if _CODING_KW.search(msg):
        return RouteDecision(TASK_CODING, "偵測到程式撰寫意圖")

    # 9. 架構設計
    if _ARCHITECTURE_KW.search(msg):
        return RouteDecision(TASK_ARCHITECTURE, "偵測到架構 / 系統設計意圖")

    # 10. 摘要
    if _SUMMARY_KW.search(msg):
        return RouteDecision(TASK_SUMMARY, "偵測到摘要 / 重點整理意圖")

    # 11. 規劃
    if _PLANNING_KW.search(msg):
        return RouteDecision(TASK_PLANNING, "偵測到規劃 / 路線圖意圖")

    # 12. 大型分析（長篇含程式碼片段 → 當架構分析）
    if _ANALYSIS_KW.search(msg) or (_CODE_HINT.search(msg) and len(msg) > 400):
        return RouteDecision(TASK_ARCHITECTURE, "偵測到分析 / 長篇內容 → 架構分析")

    # 13. 搜尋 / 資訊查詢
    if _SEARCH_KW.search(msg):
        return RouteDecision(TASK_SEARCH, "偵測到資訊查詢意圖")

    # 14. 角色扮演（sexline 核心）
    if _ROLEPLAY_KW.search(msg):
        return RouteDecision(TASK_ROLEPLAY, "偵測到角色扮演 / 親密互動訊號")

    # 15. 預設：一般聊天
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
