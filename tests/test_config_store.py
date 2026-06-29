from bot.config_store import ConfigStore


def test_config_store_creates_defaults(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")

    config = store.load()

    assert config["welcome"]["enabled"] is True
    assert config["features"]["welcome"] is True
    assert config["features"]["keyword_replies"] is True
    assert config["features"]["banned_words"] is True
    assert config["features"]["ai_chat"] is True
    assert config["features"]["ai_image"] is True
    assert config["features"]["ai_video"] is True
    assert config["bot"]["qq"] == ""
    assert config["bot"]["hosting_enabled"] is False
    assert config["bot"]["login_state"] == "not_configured"
    assert config["moderation"]["strike_limit"] == 2
    assert config["moderation"]["window_hours"] == 24
    assert config["keywords"] == {}
    assert config["banned_words"] == []


def test_config_store_persists_updates(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    config = store.load()
    config["keywords"] = {"hello": "world"}

    store.save(config)

    assert ConfigStore(tmp_path / "bot_config.json").load()["keywords"] == {"hello": "world"}
