from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover - optional but installed in project venv
    yaml = None

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

HERMES_HOME = Path.home() / "AppData" / "Local" / "hermes"
HERMES_CONFIG = HERMES_HOME / "config.yaml"
HERMES_MODELS_CACHE = HERMES_HOME / "provider_models_cache.json"
HERMES_ENV = HERMES_HOME / ".env"

if load_dotenv and HERMES_ENV.exists():
    load_dotenv(HERMES_ENV, override=False)


@dataclass(frozen=True)
class ModelChoice:
    id: str
    label: str
    provider: str
    model: str
    base_url: str
    api_key_env: str | None = None
    kind: str = "api"
    available: bool = True

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("api_key_env", None)
        data["requires_key"] = bool(self.api_key_env)
        data["available"] = self.is_available()
        return data

    def is_available(self) -> bool:
        if self.kind == "local":
            return True
        if not self.api_key_env:
            return True
        return bool(os.getenv(self.api_key_env, "").strip())


def _safe_slug(text: str) -> str:
    return (
        text.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(":", "-")
        .replace("_", "-")
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _local_models_from_hermes_config() -> list[ModelChoice]:
    config = _load_yaml(HERMES_CONFIG)
    choices: list[ModelChoice] = []
    for item in config.get("custom_providers") or []:
        if not isinstance(item, dict):
            continue
        base_url = str(item.get("base_url") or "").strip()
        model = str(item.get("model") or "").strip()
        name = str(item.get("name") or model or "Local Model").strip()
        if not base_url or not model:
            continue
        choices.append(
            ModelChoice(
                id=f"local:{_safe_slug(name)}",
                label=name,
                provider="local",
                model=model,
                base_url=base_url.rstrip("/"),
                kind="local",
            )
        )
    return choices


def _api_models_from_cache(limit_per_provider: int = 8) -> list[ModelChoice]:
    if not HERMES_MODELS_CACHE.exists():
        return []

    provider_specs = {
        "openrouter": ("OpenRouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
        "openai-api": ("OpenAI API", "https://api.openai.com/v1", "OPENAI_API_KEY"),
        "openai-codex": ("OpenAI Codex", "https://api.openai.com/v1", "OPENAI_API_KEY"),
        "gemini": ("Gemini", "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
        "deepseek": ("DeepSeek", "https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
        "xai-oauth": ("xAI / Grok", "https://api.x.ai/v1", "XAI_API_KEY"),
    }

    try:
        raw = json.loads(HERMES_MODELS_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return []

    choices: list[ModelChoice] = []
    for provider, spec in provider_specs.items():
        if provider not in raw:
            continue
        label_prefix, base_url, api_key_env = spec
        models = raw.get(provider, {}).get("models") or []
        for model in models[:limit_per_provider]:
            if not isinstance(model, str):
                continue
            choices.append(
                ModelChoice(
                    id=f"{provider}:{_safe_slug(model)}",
                    label=f"{label_prefix} · {model}",
                    provider=provider,
                    model=model,
                    base_url=base_url,
                    api_key_env=api_key_env,
                    kind="api",
                )
            )
    return choices


def get_model_choices() -> list[ModelChoice]:
    local = _local_models_from_hermes_config()
    api = _api_models_from_cache()

    if not local:
        local = [
            ModelChoice(
                id="local:ollama-default",
                label="Local Ollama · qwen2.5:7b",
                provider="local",
                model="qwen2.5:7b",
                base_url="http://127.0.0.1:11434/v1",
                kind="local",
            )
        ]

    if not api:
        api = [
            ModelChoice(
                id="openrouter:claude-haiku",
                label="OpenRouter · anthropic/claude-haiku-4.5",
                provider="openrouter",
                model="anthropic/claude-haiku-4.5",
                base_url="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY",
                kind="api",
            )
        ]

    # 加入 DeepSeek 備援（provider_models_cache 有的時候會由 _api_models_from_cache 自動加入）
    api_has_deepseek = any(c.provider == "deepseek" for c in api)
    if not api_has_deepseek and os.getenv("DEEPSEEK_API_KEY", "").strip():
        deepseek_models = [
            ("deepseek-chat", "DeepSeek · deepseek-chat"),
            ("deepseek-reasoner", "DeepSeek · deepseek-reasoner"),
        ]
        for model, label in deepseek_models:
            api.append(ModelChoice(
                id=f"deepseek:{_safe_slug(model)}",
                label=label,
                provider="deepseek",
                model=model,
                base_url="https://api.deepseek.com/v1",
                api_key_env="DEEPSEEK_API_KEY",
                kind="api",
            ))

    return [*local, *api]


def get_model_by_id(model_id: str | None) -> ModelChoice:
    choices = get_model_choices()
    if model_id:
        for choice in choices:
            if choice.id == model_id:
                return choice
    return choices[0]
