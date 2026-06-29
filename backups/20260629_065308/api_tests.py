from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    for test in [
        test_models_endpoint_lists_hermes_like_choices,
        test_model_get_and_post_switches_current_model,
        test_invalid_model_rejected,
    ]:
        test()
        print(f"PASS {test.__name__}")
    print("All backend API tests passed.")
