from bot.cloud_runtime import RuntimeManager, build_lagrange_appsettings, sanitize_log_text
from bot.config_store import ConfigStore


def test_build_lagrange_appsettings_uses_reverse_websocket():
    config = build_lagrange_appsettings("123456", "127.0.0.1", 18080)

    assert config["Account"]["Uin"] == 123456
    assert config["Account"]["Protocol"] == "Linux"
    assert config["Account"]["AutoReconnect"] is True
    assert config["Implementations"] == [
        {
            "Type": "ReverseWebSocket",
            "Host": "127.0.0.1",
            "Port": 18080,
            "Suffix": "/onebot/v11/ws",
            "ReconnectInterval": 5000,
            "HeartBeatInterval": 5000,
            "HeartBeatEnable": True,
            "AccessToken": "",
        }
    ]


def test_sanitize_log_text_redacts_secrets():
    text = "Authorization: Bearer sk-test-redaction-value-1234567890 password=abc123 API_KEY=secret"

    redacted = sanitize_log_text(text)

    assert "sk-test" not in redacted
    assert "abc123" not in redacted
    assert "secret" not in redacted
    assert "[redacted]" in redacted


def test_runtime_manager_saves_account_and_lagrange_config(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    runtime = RuntimeManager(
        store,
        data_dir=tmp_path / "lagrange",
        lagrange_bin=tmp_path / "missing-lagrange",
        spawn_enabled=False,
    )

    state = runtime.save_account("123456")

    config = store.load()
    assert state["login_state"] == "configured"
    assert config["bot"]["qq"] == "123456"
    assert (tmp_path / "lagrange" / "appsettings.json").exists()


def test_runtime_manager_start_and_stop_hosting_without_spawning(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    runtime = RuntimeManager(
        store,
        data_dir=tmp_path / "lagrange",
        lagrange_bin=tmp_path / "missing-lagrange",
        spawn_enabled=False,
    )
    runtime.save_account("123456")

    started = runtime.start_hosting()
    stopped = runtime.stop_hosting()

    assert started["hosting_enabled"] is True
    assert started["login_state"] == "waiting_qr"
    assert stopped["hosting_enabled"] is False
    assert stopped["login_state"] == "configured"


def test_runtime_logs_are_sanitized(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    runtime = RuntimeManager(
        store,
        data_dir=tmp_path / "lagrange",
        lagrange_bin=tmp_path / "missing-lagrange",
        spawn_enabled=False,
    )

    runtime.log("token sk-test-redaction-value-1234567890 password=abc")

    logs = runtime.recent_logs()
    assert "sk-test" not in logs[0]
    assert "abc" not in logs[0]
    assert "[redacted]" in logs[0]
