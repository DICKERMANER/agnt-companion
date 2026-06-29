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
)
from database import Companion, User, get_db, init_db
from model_registry import get_model_by_id, get_model_choices
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
    allow_origins=["*"],
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


class ModelSwitchRequest(BaseModel):
    model_id: str = Field(..., min_length=1)


class DiamondsSetRequest(BaseModel):
    # 測試板：允許使用者自行輸入鑽石餘額。0~999999 之間。
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
    # 自動選取第一個可用模型，避免前端載入時 /models.current_model 為 null
    if CURRENT_MODEL_ID is None:
        choices = get_model_choices()
        if choices:
            CURRENT_MODEL_ID = choices[0].id


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
    return {"ok": True}


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
    """測試板專用：使用者自行設定鑽石餘額。"""
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
    """Import a raw Soul.md document (with YAML frontmatter) as a new/updated soul."""
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

    # 付費鎖：每聊一句先扣 1 鑽，餘額不足直接攔截
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

    # 情緒評判 Hook
    sentiment = analyze_sentiment(payload.message)
    companion.favorability_score = max(0, min(100, companion.favorability_score + sentiment_delta(sentiment)))
    companion.relationship_stage = map_relationship_stage(companion.favorability_score)
    db.add(companion)
    db.commit()
    db.refresh(companion)

    # 動態 Prompt 注入
    active_soul = get_soul(companion.soul_id)
    system_prompt = build_dynamic_system_prompt(companion.relationship_stage, active_soul)
    user_message = payload.message
    if payload.action_prompt:
        user_message = f"[快捷操作]{payload.action_prompt}\n[用戶訊息]{payload.message}"

    persona_profile = payload.persona_profile
    if not persona_profile and persona_store.has_saved_persona():
        persona_profile = persona_store.load_persona()

    if persona_profile:
        system_prompt = f"角色名稱: {persona_profile.get('name')}\n" \
                        f"生日: {persona_profile.get('birthday')}\n" \
                        f"性格核心: {persona_profile.get('personality')}\n\n" \
                        f"{system_prompt}"

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
    )
