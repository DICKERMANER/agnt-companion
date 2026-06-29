from fastapi.testclient import TestClient

import ai_engine
from main import app

client = TestClient(app)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_models_endpoint_lists_hermes_like_choices() -> None:
    response = client.get("/models")
    assert_true(response.status_code == 200, "/models should return 200")
    data = response.json()
    assert_true("models" in data, "/models should include models list")
    assert_true("current_model" in data, "/models should include current_model")
    assert_true(len(data["models"]) >= 4, "/models should expose API models plus local models")
    assert_true(any(m["provider"] == "local" for m in data["models"]), "local models should be present")
    assert_true(any(m["provider"] != "local" for m in data["models"]), "cloud/API models should be present")


def test_model_get_and_post_switches_current_model() -> None:
    models = client.get("/models").json()["models"]
    target = next(m for m in models if m["provider"] == "local")
    response = client.post("/model", json={"model_id": target["id"]})
    assert_true(response.status_code == 200, "/model POST should return 200")
    data = response.json()
    assert_true(data["current_model"]["id"] == target["id"], "/model POST should switch current model")

    current = client.get("/model").json()
    assert_true(current["current_model"]["id"] == target["id"], "/model GET should return switched model")


def test_invalid_model_rejected() -> None:
    response = client.post("/model", json={"model_id": "missing-model"})
    assert_true(response.status_code == 404, "invalid model should return 404")


def test_chat_accepts_runtime_model_options_when_billing_locked() -> None:
    user_id = "runtime_options_user"
    # Drain demo credits deterministically so the endpoint returns before calling a real LLM.
    for _ in range(21):
        response = client.post(
            "/webhook/chat",
            json={
                "user_id": user_id,
                "message": "測試模型選項",
                "thinking_enabled": True,
                "fast_mode": False,
                "reasoning_effort": "high",
            },
        )
    assert_true(response.status_code == 200, "chat should accept model runtime options")
    data = response.json()
    assert_true(data["provider"] == "billing-lock", "test should avoid real LLM calls via billing lock")
    assert_true(data["reasoning_effort"] == "high", "response should echo reasoning effort")
    assert_true(data["thinking_enabled"] is True, "response should echo thinking toggle")
    assert_true(data["fast_mode"] is False, "response should echo fast mode toggle")


def test_invalid_reasoning_effort_rejected() -> None:
    response = client.post(
        "/webhook/chat",
        json={"user_id": "bad_runtime_options", "message": "hi", "reasoning_effort": "extreme"},
    )
    assert_true(response.status_code == 422, "invalid reasoning effort should return validation error")


def test_persona_endpoint_saves_custom_soul_profile() -> None:
    payload = {
        "name": "Rosie",
        "birthday": "1997-02-11",
        "personality": "浪漫、黏人、藝術家靈魂",
        "soul_md": "# Soul\n你是 Rosie，記得自己的生日與個性。",
    }
    response = client.post("/persona", json=payload)
    assert_true(response.status_code == 200, "/persona POST should save custom persona")
    data = response.json()
    assert_true(data["persona"]["name"] == "Rosie", "saved persona should echo name")
    assert_true(data["persona"]["birthday"] == "1997-02-11", "saved persona should echo birthday")

    current = client.get("/persona").json()
    assert_true(current["persona"]["personality"] == payload["personality"], "/persona GET should return saved persona")


def test_chat_injects_persona_and_runtime_options_without_real_llm() -> None:
    captured = {}

    async def fake_generate_reply(system_prompt, user_message, prefer="local", model_choice=None, runtime_options=None, persona_profile=None):
        captured["system_prompt"] = system_prompt
        captured["runtime_options"] = runtime_options
        captured["persona_profile"] = persona_profile
        return ai_engine.EngineResponse(text="ok", provider="fake", model="fake-model")

    original = ai_engine.generate_reply
    import main as main_module
    original_main = main_module.generate_reply
    ai_engine.generate_reply = fake_generate_reply
    main_module.generate_reply = fake_generate_reply
    try:
        response = client.post(
            "/webhook/chat",
            json={
                "user_id": "persona_runtime_user",
                "message": "hi",
                "thinking_enabled": True,
                "fast_mode": True,
                "reasoning_effort": "max",
                "persona_profile": {
                    "name": "Mina",
                    "birthday": "2000-03-24",
                    "personality": "冷艷、佔有慾強",
                    "soul_md": "# Soul\nMina has precise memory.",
                },
            },
        )
    finally:
        ai_engine.generate_reply = original
        main_module.generate_reply = original_main

    assert_true(response.status_code == 200, "chat should accept persona/runtime payload")
    data = response.json()
    assert_true(data["provider"] == "fake", "chat should use patched fake provider")
    assert_true(data["reasoning_effort"] == "max", "response should echo max reasoning effort")
    assert_true(captured["runtime_options"]["fast_mode"] is True, "runtime options should reach AI engine")
    assert_true(captured["persona_profile"]["name"] == "Mina", "persona should reach AI engine")
    assert_true("Mina" in captured["system_prompt"], "persona name should be injected into prompt")


if __name__ == "__main__":
    for test in [
        test_models_endpoint_lists_hermes_like_choices,
        test_model_get_and_post_switches_current_model,
        test_invalid_model_rejected,
        test_chat_accepts_runtime_model_options_when_billing_locked,
        test_invalid_reasoning_effort_rejected,
        test_persona_endpoint_saves_custom_soul_profile,
        test_chat_injects_persona_and_runtime_options_without_real_llm,
    ]:
        test()
        print(f"PASS {test.__name__}")
    print("All backend API tests passed.")
