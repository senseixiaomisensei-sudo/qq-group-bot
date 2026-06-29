from fastapi.testclient import TestClient

from bot.admin_app import create_admin_app
from bot.cloud_runtime import RuntimeManager
from bot.config_store import ConfigStore


def make_client(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    runtime = RuntimeManager(
        store,
        data_dir=tmp_path / "lagrange",
        lagrange_bin=tmp_path / "missing-lagrange",
        spawn_enabled=False,
    )
    return TestClient(create_admin_app(store, runtime=runtime))


def test_health_reports_cloud_service(tmp_path):
    client = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["bot_state"]["login_state"] == "not_configured"
    assert "ai_configured" in response.json()


def test_status_account_and_hosting_round_trip(tmp_path):
    client = make_client(tmp_path)

    account = client.post("/bot/account", json={"qq": "123456"})
    start = client.post("/bot/hosting/start")
    status = client.get("/status")
    stop = client.post("/bot/hosting/stop")

    assert account.status_code == 200
    assert account.json()["login_state"] == "configured"
    assert start.status_code == 200
    assert start.json()["hosting_enabled"] is True
    assert start.json()["login_state"] == "waiting_qr"
    assert status.json()["hosting_enabled"] is True
    assert status.json()["group_count"] == 0
    assert stop.json()["hosting_enabled"] is False


def test_config_endpoint_updates_features_and_quick_settings(tmp_path):
    client = make_client(tmp_path)

    response = client.post(
        "/config",
        json={
            "features": {"welcome": False, "ai_video": False},
            "welcome": {"enabled": False, "message": "Hi {nickname}"},
            "banned_words": ["bad"],
            "keywords": {"ping": "pong"},
        },
    )

    assert response.status_code == 200
    payload = client.get("/config").json()
    assert payload["features"]["welcome"] is False
    assert payload["features"]["ai_video"] is False
    assert payload["welcome"]["message"] == "Hi {nickname}"
    assert payload["banned_words"] == ["bad"]
    assert payload["keywords"] == {"ping": "pong"}


def test_api_status_masks_key(tmp_path, monkeypatch):
    monkeypatch.setenv("AGNES_API_KEY", "sk-test-redaction-value-1234567890")
    client = make_client(tmp_path)

    response = client.get("/api-status")

    assert response.status_code == 200
    assert response.json()["configured"] is True
    assert response.json()["key_preview"].startswith("sk-")
    assert "redaction" not in response.json()["key_preview"]


def test_logs_endpoint_redacts_secrets(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    runtime = RuntimeManager(
        store,
        data_dir=tmp_path / "lagrange",
        lagrange_bin=tmp_path / "missing-lagrange",
        spawn_enabled=False,
    )
    runtime.log("api_key=sk-test-redaction-value-1234567890 password=abc")
    client = TestClient(create_admin_app(store, runtime=runtime))

    response = client.get("/logs")

    assert response.status_code == 200
    joined = "\n".join(response.json()["items"])
    assert "sk-test" not in joined
    assert "abc" not in joined
    assert "[redacted]" in joined


def test_keyword_config_round_trip(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/config/keywords", json={"items": {"ping": "pong"}})

    assert response.status_code == 200
    assert client.get("/config/keywords").json()["items"] == {"ping": "pong"}


def test_banned_words_round_trip(tmp_path):
    client = make_client(tmp_path)

    response = client.post("/config/banned-words", json={"items": ["bad"]})

    assert response.status_code == 200
    assert client.get("/config/banned-words").json()["items"] == ["bad"]
