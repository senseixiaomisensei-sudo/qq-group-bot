from datetime import datetime, timezone

from bot.config_store import ConfigStore
from bot.moderation import ModerationService


def test_banned_word_first_hit_warns(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    config = store.load()
    config["banned_words"] = ["bad"]
    store.save(config)
    service = ModerationService(store)

    result = service.check_message("100", "200", "this is bad", now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert result.action == "warn"
    assert result.strikes == 1
    assert "bad" in result.word


def test_banned_word_second_hit_kicks_within_window(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    config = store.load()
    config["banned_words"] = ["bad"]
    store.save(config)
    service = ModerationService(store)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    service.check_message("100", "200", "bad once", now=now)
    result = service.check_message("100", "200", "bad twice", now=now)

    assert result.action == "kick"
    assert result.strikes == 2


def test_safe_message_is_allowed(tmp_path):
    store = ConfigStore(tmp_path / "bot_config.json")
    service = ModerationService(store)

    result = service.check_message("100", "200", "hello")

    assert result.action == "allow"
    assert result.strikes == 0
