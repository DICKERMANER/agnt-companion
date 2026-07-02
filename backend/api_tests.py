from fastapi.testclient import TestClient

import os

# 測試時一律走 stub LLM，避免打到本機 ollama 慢推理導致逾時卡死。
os.environ["COMPANION_FAKE_LLM"] = "1"

import ai_engine
from database import init_db
from main import app

# Tests must be runnable standalone — don't rely on a previous `uvicorn` run
# having already created the SQLite tables via the FastAPI startup event.
init_db()

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


def test_reasoning_effort_accepts_full_range() -> None:
    for effort in ["minimal", "low", "medium", "high", "max"]:
        response = client.post(
            "/webhook/chat",
            json={"user_id": f"effort_{effort}_user", "message": "hi", "reasoning_effort": effort},
        )
        assert_true(response.status_code == 200, f"reasoning_effort '{effort}' should be accepted")
        assert_true(response.json()["reasoning_effort"] == effort, f"response should echo '{effort}'")


def test_souls_endpoint_lists_default_soul() -> None:
    response = client.get("/souls")
    assert_true(response.status_code == 200, "/souls should return 200")
    data = response.json()
    assert_true(len(data["souls"]) >= 1, "/souls should always expose at least the default soul")
    assert_true(any(s["id"] == "nova" for s in data["souls"]), "default soul should be the original 'nova' persona")


def test_souls_crud_round_trip() -> None:
    create_payload = {
        "id": "test-companion",
        "name": "Aria",
        "birthday": "1999-01-01",
        "zodiac": "摩羯座",
        "personality": "溫柔、體貼、喜歡甜點",
        "system_prompt_base": "你是 Aria，一位原創的虛擬陪伴角色。",
    }
    create_response = client.post("/souls", json=create_payload)
    assert_true(create_response.status_code == 200, "/souls POST should create a new soul")
    assert_true(create_response.json()["soul"]["id"] == "test-companion", "created soul id should match")

    detail_response = client.get("/souls/test-companion")
    assert_true(detail_response.status_code == 200, "/souls/{id} should return the created soul")
    detail = detail_response.json()
    assert_true(detail["name"] == "Aria", "soul detail should include name")
    assert_true("Aria" in detail["markdown"], "soul detail should expose raw markdown for export")

    delete_response = client.delete("/souls/test-companion")
    assert_true(delete_response.status_code == 200, "/souls/{id} DELETE should remove a custom soul")

    missing_response = client.get("/souls/test-companion")
    assert_true(missing_response.status_code == 404, "deleted soul should no longer be retrievable")


def test_souls_import_markdown() -> None:
    raw_markdown = (
        '---\n'
        'name: "Imported Companion"\n'
        'birthday: "2000-05-05"\n'
        'zodiac: "金牛座"\n'
        'personality: "穩重、可靠"\n'
        '---\n'
        '你是一位透過 Soul.md 匯入的原創陪伴角色。\n'
    )
    response = client.post("/souls/import", json={"id": "imported-companion", "markdown": raw_markdown})
    assert_true(response.status_code == 200, "/souls/import should accept a raw Soul.md document")
    assert_true(response.json()["soul"]["name"] == "Imported Companion", "imported soul should parse frontmatter name")

    detail = client.get("/souls/imported-companion").json()
    assert_true(detail["zodiac"] == "金牛座", "imported soul should parse frontmatter zodiac")

    client.delete("/souls/imported-companion")  # cleanup


def test_default_soul_cannot_be_deleted() -> None:
    response = client.delete("/souls/nova")
    assert_true(response.status_code == 400, "the default soul should be protected from deletion")


def test_persona_endpoint_saves_custom_soul_profile() -> None:
    payload = {
        "name": "Stellar",
        "birthday": "2002-08-19",
        "personality": "浪漫、黏人、藝術家靈魂",
        "soul_md": "# Soul\n你是 Stellar，記得自己的生日與個性。",
    }
    response = client.post("/persona", json=payload)
    assert_true(response.status_code == 200, "/persona POST should save custom persona")
    data = response.json()
    assert_true(data["persona"]["name"] == "Stellar", "saved persona should echo name")
    assert_true(data["persona"]["birthday"] == "2002-08-19", "saved persona should echo birthday")

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
                "reasoning_effort": "high",
                "persona_profile": {
                    "name": "Mina",
                    "birthday": "2000-03-24",
                    "personality": "冷艷、佔有慾強",
                    "soul_md": "# Soul\nMina has precise memory.",
                },
            },
        )
        assert_true(response.status_code == 200, f"chat should accept persona/runtime payload: {response.text}")
    finally:
        ai_engine.generate_reply = original
        main_module.generate_reply = original_main

    assert_true(response.status_code == 200, "chat should accept persona/runtime payload")
    data = response.json()
    assert_true(data["provider"] == "fake", "chat should use patched fake provider")
    assert_true(data["reasoning_effort"] == "high", "response should echo max reasoning effort")
    assert_true(captured["runtime_options"]["fast_mode"] is True, "runtime options should reach AI engine")
    assert_true(captured["persona_profile"]["name"] == "Mina", "persona should reach AI engine")
    assert_true("Mina" in captured["system_prompt"], "persona name should be injected into prompt")


def test_set_diamonds_lets_user_input_balance() -> None:
    # 測試板：使用者可自行設定鑽石餘額。
    res = client.post("/state/diamonds_user/diamonds", json={"diamonds_balance": 777})
    assert_true(res.status_code == 200, "/state/{id}/diamonds POST should return 200")
    assert_true(res.json()["diamonds_balance"] == 777, "diamonds balance should be updated to input value")

    state = client.get("/state/diamonds_user").json()
    assert_true(state["diamonds_balance"] == 777, "state should reflect manually set diamonds")

    bad = client.post("/state/diamonds_user/diamonds", json={"diamonds_balance": -5})
    assert_true(bad.status_code == 422, "negative diamonds should be rejected")


def test_prompts_endpoint_lists_all_templates() -> None:
    response = client.get("/prompts")
    assert_true(response.status_code == 200, "prompts endpoint should return 200")
    data = response.json()["prompts"]
    from ai_router import ALL_TASKS
    for task in ALL_TASKS:
        assert_true(data.get(task) is True, f"prompt template for '{task}' should exist")
    assert_true(data.get("_base:system.md") is True, "system.md base should exist")


def test_prompt_router_selects_template_per_task() -> None:
    from ai_router import ALL_TASKS
    for task in ALL_TASKS:
        response = client.get(f"/prompts/{task}")
        assert_true(response.status_code == 200, f"/prompts/{task} should return 200")
        template = response.json()["template"]
        assert_true(len(template) > 20, f"template for '{task}' should have content")


def test_chat_routes_to_correct_prompt_template() -> None:
    """webhook 依訊息內容選對 Prompt Template（Phase 2 端到端）。"""
    cases = {
        "translate": "幫我把這句翻譯成英文：你好",
        "debug": "程式噴 error traceback",
        "financial": "台積電股價會漲嗎",
        "python": "寫一個 python 腳本",
        "roleplay": "寶貝抱抱我",
        "chat": "晚餐吃什麼",
    }
    for i, (expected_task, msg) in enumerate(cases.items()):
        response = client.post(
            "/webhook/chat",
            json={"user_id": f"prompt_route_{i}", "message": msg, "auto_route": True},
        )
        assert_true(response.status_code == 200, f"chat should succeed for '{expected_task}'")
        data = response.json()
        assert_true(
            data["routed_task"] == expected_task,
            f"'{msg}' should route to task '{expected_task}', got '{data['routed_task']}'",
        )
        assert_true(
            data["routed_prompt"] == f"{expected_task}.md",
            f"'{msg}' should load '{expected_task}.md', got '{data['routed_prompt']}'",
        )


if __name__ == "__main__":
    for test in [
        test_models_endpoint_lists_hermes_like_choices,
        test_model_get_and_post_switches_current_model,
        test_invalid_model_rejected,
        test_chat_accepts_runtime_model_options_when_billing_locked,
        test_invalid_reasoning_effort_rejected,
        test_reasoning_effort_accepts_full_range,
        test_souls_endpoint_lists_default_soul,
        test_souls_crud_round_trip,
        test_souls_import_markdown,
        test_default_soul_cannot_be_deleted,
        test_persona_endpoint_saves_custom_soul_profile,
        test_chat_injects_persona_and_runtime_options_without_real_llm,
        test_set_diamonds_lets_user_input_balance,
        test_prompts_endpoint_lists_all_templates,
        test_prompt_router_selects_template_per_task,
        test_chat_routes_to_correct_prompt_template,
    ]:
        test()
        print(f"PASS {test.__name__}")
    print("All backend API tests passed.")
