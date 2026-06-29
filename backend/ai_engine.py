from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

import httpx

Sentiment = Literal["positive", "negative", "neutral"]


@dataclass
class EngineResponse:
    text: str
    provider: str
    model: str | None = None


POSITIVE_WORDS = {
    "喜歡", "愛", "開心", "謝謝", "可愛", "想你", "讚", "棒", "幸福", "喜悅", "支持", "抱抱"
}
NEGATIVE_WORDS = {
    "討厭", "煩", "爛", "生氣", "難過", "失望", "痛苦", "滾", "不爽", "崩潰", "垃圾"
}


def analyze_sentiment(message: str) -> Sentiment:
    score = 0
    for w in POSITIVE_WORDS:
        if w in message:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in message:
            score -= 1

    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def sentiment_delta(sentiment: Sentiment) -> int:
    if sentiment == "positive":
        return 4
    if sentiment == "negative":
        return -5
    return 1


def map_relationship_stage(favorability_score: int) -> str:
    if favorability_score < 20:
        return "cold"
    if favorability_score < 50:
        return "flirty"
    if favorability_score < 80:
        return "devoted"
    return "lover"


def build_dynamic_system_prompt(stage: str, soul) -> str:
    stage_prompt = {
        "cold": "你現在與使用者關係偏冷淡，語氣克制但不失禮。",
        "flirty": "你與使用者進入曖昧期，語氣更親近，偶爾主動關心。",
        "devoted": "你對使用者有明顯依賴與信任感，互動熱度明顯提升。",
        "lover": "你與使用者處於完全熱戀狀態，語氣深情且有強烈陪伴感。",
    }.get(stage, "你與使用者維持穩定陪伴關係。")

    embody_rule = (
        "每次回覆都必須使用 embody 模式："
        "先用一段半形括號 () 描述細膩肢體動作與神態，"
        "再接續自然口語對話。"
    )

    soul_header = (
        f"角色名稱: {soul.name}\n"
        f"生日: {soul.birthday} ({soul.zodiac})\n"
        f"性格核心: {soul.personality}\n"
        f"底層設定: {soul.system_prompt_base}\n"
    )

    return f"{soul_header}\n[關係階段指令]\n{stage_prompt}\n\n[系統規則]\n{embody_rule}"


async def call_openai_compatible(
    system_prompt: str,
    user_message: str,
    *,
    base_url: str,
    model: str,
    provider: str,
    api_key: str | None = None,
) -> EngineResponse:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    if not endpoint.endswith("/v1/chat/completions") and "/v1/" not in endpoint:
        endpoint = f"{base_url.rstrip('/')}/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.85,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=35.0) as client:
        resp = await client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        message = data.get("choices", [{}])[0].get("message", {})
        text = (message.get("content") or "").strip()
        if not text:
            reasoning = (message.get("reasoning") or "").strip()
            finish_reason = data.get("choices", [{}])[0].get("finish_reason", "unknown")
            # 有些 Ollama / reasoning 模型會只吐 reasoning、不吐 content；前端看起來就像「按鈕沒反應」。
            # 這裡回傳可讀診斷，避免空泡泡。
            text = (
                f"(她停頓了一下，低頭確認模型狀態) 模型已連接，但這次沒有產生正式回覆 content。"
                f"\n模型：{model}"
                f"\n結束原因：{finish_reason}"
                f"\n診斷：若一直出現，請切換模型或調高輸出長度；目前後端 endpoint 是 {endpoint}。"
            )
            if reasoning:
                text += f"\n模型只輸出了 reasoning 片段：{reasoning[:180]}..."
        return EngineResponse(text=text, provider=provider, model=model)


async def call_local_llm(system_prompt: str, user_message: str) -> EngineResponse:
    base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://127.0.0.1:8080")
    model = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:7b")
    return await call_openai_compatible(
        system_prompt,
        user_message,
        base_url=base_url,
        model=model,
        provider="local",
    )


async def call_cloud_llm(system_prompt: str, user_message: str) -> EngineResponse:
    cloud_url = os.getenv("CLOUD_API_URL", "").strip()
    cloud_key = os.getenv("CLOUD_API_KEY", "").strip()
    cloud_model = os.getenv("CLOUD_MODEL", "gpt-4.1-mini")

    if not cloud_url or not cloud_key:
        return EngineResponse(
            text="(她輕輕抬眼看你，指尖在你掌心畫圈) 我現在雲端通道沒接上，先用本地模式陪你聊，好嗎？",
            provider="cloud-fallback",
            model=cloud_model,
        )

    payload = {
        "model": cloud_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.85,
    }
    headers = {"Authorization": f"Bearer {cloud_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.post(cloud_url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        # 相容 OpenAI-like schema
        if "choices" in data:
            text = data["choices"][0]["message"]["content"]
        else:
            text = data.get("output_text", "")

        return EngineResponse(text=text, provider="cloud", model=cloud_model)


async def generate_reply(
    system_prompt: str,
    user_message: str,
    prefer: str = "local",
    model_choice=None,
    runtime_options: dict | None = None,
    persona_profile: dict | None = None
) -> EngineResponse:
    # 測試 / 離線模式：設 COMPANION_FAKE_LLM=1 時，直接回傳 stub，
    # 不打任何真實模型端點（避免 CI / 無網路 / ollama 慢推理時卡住）。
    if os.getenv("COMPANION_FAKE_LLM", "").strip() in {"1", "true", "True"}:
        model_name = getattr(model_choice, "model", None) or "fake-llm"
        return EngineResponse(
            text="(她微微歪頭，眼神溫柔地落在你身上) 嗯…我在喔，慢慢說給我聽。",
            provider="fake-llm",
            model=model_name,
        )

    if model_choice is not None:
        api_key = os.getenv(model_choice.api_key_env or "", "").strip() or None
        try:
            return await call_openai_compatible(
                system_prompt,
                user_message,
                base_url=model_choice.base_url,
                model=model_choice.model,
                provider=model_choice.provider,
                api_key=api_key,
            )
        except Exception:
            if model_choice.kind != "local":
                raise
            return await call_cloud_llm(system_prompt, user_message)

    if prefer == "cloud":
        return await call_cloud_llm(system_prompt, user_message)

    try:
        return await call_local_llm(system_prompt, user_message)
    except Exception:
        # 本地失敗時自動 fallback 雲端
        return await call_cloud_llm(system_prompt, user_message)
