from __future__ import annotations

from typing import Literal, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai_engine import (
    analyze_sentiment,
    build_dynamic_system_prompt,
    generate_reply,
    map_relationship_stage,
    sentiment_delta,
    stage_instruction,
    soul_block,
)
from database import Companion, User, get_db, init_db
from model_registry import get_model_by_id, get_model_choices
from ai_router import route_model, classify_task
import prompt_router
from monetization import INSUFFICIENT_BALANCE_MESSAGE, consume_one_diamond
import persona_store
from soul_manager import (
    DEFAULT_SOUL_ID,
    delete_soul,
    get_soul,
    get_soul_raw_markdown,
    load_all_souls,
    save_soul,
    save_soul_markdown,
)

app = FastAPI(title="Cyber Companion SaaS", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dickermaner.github.io",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8002",
        "http://127.0.0.1:8002",
    ],
    allow_origin_regex=r"^https://dickermaner\.github\.io$|^https://.*\.trycloudflare\.com$|^http://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}):(5500|8002)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_MODEL_ID: str | None = None


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    provider: str = Field(default="local")
    thinking_enabled: bool = False
    fast_mode: bool = False
    reasoning_effort: Literal["minimal", "low", "medium", "high", "max"] = "medium"
    action_prompt: Optional[str] = None
    persona_profile: Optional[dict] = None
    auto_route: bool = True  # AI Router：自動依訊息內容挑模型（使用者不用選）


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model_id: str | None = None
    model_name: str | None = None
    diamonds_balance: int
    favorability_score: int
    relationship_stage: str
    reasoning_effort: str | None = None
    thinking_enabled: bool = False
    fast_mode: bool = False
    avatar: str = "👑"
    routed_task: str | None = None   # AI Router 判定的任務類型
    routed_reason: str | None = None  # AI Router 選擇理由
    routed_prompt: str | None = None  # Prompt Router 載入的 template 名稱


class ModelSwitchRequest(BaseModel):
    model_id: str = Field(..., min_length=1)


class DiamondsSetRequest(BaseModel):
    diamonds_balance: int = Field(..., ge=0, le=999999)


class SoulSaveRequest(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    birthday: str = ""
    zodiac: str = ""
    personality: str = ""
    system_prompt_base: str = ""
    avatar: str = "👑"


class SoulImportRequest(BaseModel):
    id: str = Field(..., min_length=1)
    markdown: str = Field(..., min_length=1)


@app.on_event("startup")
def on_startup() -> None:
    global CURRENT_MODEL_ID
    init_db()
    if CURRENT_MODEL_ID is None:
        choices = get_model_choices()
        if choices:
            # 預設選雲端模型（deepseek flash），不要選可能掛掉的本地模型
            cloud_choices = [c for c in choices if c.kind != "local"]
            CURRENT_MODEL_ID = cloud_choices[0].id if cloud_choices else choices[0].id


def get_or_create_user_bundle(db: Session, user_id: str) -> tuple[User, Companion]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, diamonds_balance=20, vip_status=False)
        db.add(user)
        db.commit()
        db.refresh(user)

    companion = db.query(Companion).filter(Companion.user_id == user.id).first()
    if not companion:
        companion = Companion(user_id=user.id, soul_id=DEFAULT_SOUL_ID, favorability_score=0, relationship_stage="cold")
        db.add(companion)
        db.commit()
        db.refresh(companion)

    return user, companion


def get_current_model_choice():
    return get_model_by_id(CURRENT_MODEL_ID)


def serialize_current_model() -> dict:
    return get_current_model_choice().to_public_dict()


@app.get("/health")
def health() -> dict:
    import os
    keys = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
    env_status = {k: f"SET (len={len(os.getenv(k, ''))})" if os.getenv(k) else "NOT SET" for k in keys}
    return {"ok": True, "env": env_status}


@app.get("/debug/env")
def debug_env() -> dict:
    import os
    keys = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"]
    return {k: f"SET (len={len(os.getenv(k, ''))})" if os.getenv(k) else "NOT SET" for k in keys}


@app.get("/state/{user_id}")
def get_state(user_id: str, db: Session = Depends(get_db)) -> dict:
    user, companion = get_or_create_user_bundle(db, user_id)
    return {
        "user_id": user.user_id,
        "diamonds_balance": user.diamonds_balance,
        "vip_status": user.vip_status,
        "favorability_score": companion.favorability_score,
        "relationship_stage": companion.relationship_stage,
    }


@app.post("/state/{user_id}/diamonds")
def set_diamonds(user_id: str, payload: DiamondsSetRequest, db: Session = Depends(get_db)) -> dict:
    user, companion = get_or_create_user_bundle(db, user_id)
    user.diamonds_balance = payload.diamonds_balance
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "user_id": user.user_id,
        "diamonds_balance": user.diamonds_balance,
        "vip_status": user.vip_status,
        "favorability_score": companion.favorability_score,
        "relationship_stage": companion.relationship_stage,
    }


@app.get("/models")
def list_models() -> dict:
    return {
        "current_model": serialize_current_model(),
        "models": [choice.to_public_dict() for choice in get_model_choices()],
    }


@app.get("/prompts")
def list_prompts() -> dict:
    """列出所有任務類型的 Prompt Template 狀態（Phase 2 Prompt Router）。"""
    return {
        "prompts": prompt_router.list_available_prompts(),
        "prompts_dir": prompt_router.PROMPTS_DIR,
    }


@app.get("/prompts/{task_type}")
def get_prompt(task_type: str) -> dict:
    """取得某任務類型實際載入的 Prompt Template 內容。"""
    return {
        "task_type": task_type,
        "template": prompt_router.get_task_prompt(task_type),
        "system_base": prompt_router.get_system_base(),
    }


@app.get("/souls")
def list_souls() -> dict:
    souls = load_all_souls()
    return {
        "souls": [
            {"id": s.id, "name": s.name, "birthday": s.birthday, "zodiac": s.zodiac, "personality": s.personality, "avatar": s.avatar}
            for s in souls.values()
        ]
    }


@app.get("/souls/{soul_id}")
def get_soul_detail(soul_id: str) -> dict:
    souls = load_all_souls()
    soul = souls.get(soul_id)
    if not soul:
        raise HTTPException(status_code=404, detail="soul not found")
    return {
        "id": soul.id,
        "name": soul.name,
        "birthday": soul.birthday,
        "zodiac": soul.zodiac,
        "personality": soul.personality,
        "system_prompt_base": soul.system_prompt_base,
        "avatar": soul.avatar,
        "markdown": get_soul_raw_markdown(soul_id) or "",
    }


@app.post("/souls")
def upsert_soul(payload: SoulSaveRequest) -> dict:
    soul = save_soul(
        soul_id=payload.id or payload.name,
        name=payload.name,
        birthday=payload.birthday,
        zodiac=payload.zodiac,
        personality=payload.personality,
        system_prompt_base=payload.system_prompt_base,
        avatar=payload.avatar,
    )
    return {"status": "ok", "soul": {"id": soul.id, "name": soul.name, "birthday": soul.birthday, "avatar": soul.avatar}}


@app.post("/souls/import")
def import_soul_markdown(payload: SoulImportRequest) -> dict:
    soul = save_soul_markdown(payload.id, payload.markdown)
    return {"status": "ok", "soul": {"id": soul.id, "name": soul.name, "birthday": soul.birthday}}


@app.delete("/souls/{soul_id}")
def remove_soul(soul_id: str) -> dict:
    if soul_id == DEFAULT_SOUL_ID:
        raise HTTPException(status_code=400, detail="cannot delete the default soul")
    deleted = delete_soul(soul_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="soul not found")
    return {"status": "ok", "deleted": soul_id}


@app.get("/model")
def get_model() -> dict:
    return {"current_model": serialize_current_model()}


@app.post("/model")
def set_model(payload: ModelSwitchRequest) -> dict:
    global CURRENT_MODEL_ID
    choices = get_model_choices()
    if not any(choice.id == payload.model_id for choice in choices):
        raise HTTPException(status_code=404, detail="model not found")
    CURRENT_MODEL_ID = payload.model_id
    return {"current_model": serialize_current_model()}


@app.post("/persona")
def save_persona_profile(payload: dict) -> dict:
    saved = persona_store.save_persona(payload)
    return {"status": "ok", "persona": saved}


@app.get("/persona")
def get_persona_profile() -> dict:
    return {"persona": persona_store.load_persona()}


@app.post("/webhook/chat", response_model=ChatResponse)
async def webhook_chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    user, companion = get_or_create_user_bundle(db, payload.user_id)
    model_choice = get_current_model_choice()

    # ── AI Router：依訊息內容自動挑最適合的模型（使用者不用自己選）──
    routed_task = None
    routed_reason = None
    if payload.auto_route:
        try:
            routed_choice, decision = route_model(
                payload.message, get_model_choices(), current_choice=model_choice
            )
            if routed_choice is not None:
                model_choice = routed_choice
            routed_task = decision.task_type
            routed_reason = decision.reason
        except Exception:
            # 路由失敗絕不能擋住聊天 → 沿用當前模型
            pass

    # auto_route 關閉時仍需知道任務類型（給 Prompt Router 選 template）
    if routed_task is None:
        try:
            routed_task = classify_task(payload.message).task_type
        except Exception:
            routed_task = "roleplay"  # sexline 預設情境

    if not consume_one_diamond(db, user):
        return ChatResponse(
            reply=INSUFFICIENT_BALANCE_MESSAGE,
            provider="billing-lock",
            model_id=model_choice.id,
            model_name=model_choice.label,
            diamonds_balance=user.diamonds_balance,
            favorability_score=companion.favorability_score,
            relationship_stage=companion.relationship_stage,
            reasoning_effort=payload.reasoning_effort,
            thinking_enabled=payload.thinking_enabled,
            fast_mode=payload.fast_mode,
        )

    sentiment = analyze_sentiment(payload.message)
    companion.favorability_score = max(0, min(100, companion.favorability_score + sentiment_delta(sentiment)))
    companion.relationship_stage = map_relationship_stage(companion.favorability_score)
    db.add(companion)
    db.commit()
    db.refresh(companion)

    active_soul = get_soul(companion.soul_id)
    user_message = payload.message
    if payload.action_prompt:
        user_message = f"[快捷操作]{payload.action_prompt}\n[用戶訊息]{payload.message}"

    persona_profile = payload.persona_profile
    if not persona_profile and persona_store.has_saved_persona():
        persona_profile = persona_store.load_persona()

    # ── Prompt Router：依任務類型載入對應的模組化 Prompt Template ──
    persona_block = None
    if persona_profile:
        persona_block = (
            f"角色名稱: {persona_profile.get('name')}\n"
            f"生日: {persona_profile.get('birthday')}\n"
            f"性格核心: {persona_profile.get('personality')}"
        )

    try:
        system_prompt = prompt_router.build_system_prompt(
            routed_task,
            stage_prompt=stage_instruction(companion.relationship_stage),
            soul_block=soul_block(active_soul),
            persona_block=persona_block,
        )
        routed_prompt = f"{routed_task}.md"
    except Exception:
        # Prompt Router 失敗 → fallback 回舊的硬編組裝，絕不擋聊天
        system_prompt = build_dynamic_system_prompt(companion.relationship_stage, active_soul)
        if persona_block:
            system_prompt = f"{persona_block}\n\n{system_prompt}"
        routed_prompt = "fallback:build_dynamic_system_prompt"

    ai_result = await generate_reply(
        system_prompt,
        user_message,
        prefer=payload.provider,
        model_choice=model_choice,
        runtime_options={
            "thinking_enabled": payload.thinking_enabled,
            "fast_mode": payload.fast_mode,
            "reasoning_effort": payload.reasoning_effort
        },
        persona_profile=persona_profile
    )

    return ChatResponse(
        reply=ai_result.text,
        provider=ai_result.provider,
        model_id=model_choice.id,
        model_name=model_choice.label,
        diamonds_balance=user.diamonds_balance,
        favorability_score=companion.favorability_score,
        relationship_stage=companion.relationship_stage,
        reasoning_effort=payload.reasoning_effort,
        thinking_enabled=payload.thinking_enabled,
        fast_mode=payload.fast_mode,
        avatar=active_soul.avatar,
        routed_task=routed_task,
        routed_reason=routed_reason,
        routed_prompt=routed_prompt,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
