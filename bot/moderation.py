from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from bot.config_store import ConfigStore


@dataclass(frozen=True)
class ModerationResult:
    action: str
    word: str
    strikes: int
    message: str


class ModerationService:
    def __init__(self, store: ConfigStore):
        self.store = store

    def check_message(
        self,
        group_id: str,
        user_id: str,
        text: str,
        *,
        now: datetime | None = None,
    ) -> ModerationResult:
        config = self.store.load()
        moderation = config["moderation"]
        if not moderation.get("enabled", True):
            return ModerationResult("allow", "", 0, "")

        word = self._matched_word(text, config.get("banned_words", []))
        if not word:
            return ModerationResult("allow", "", 0, "")

        now = now or datetime.now(timezone.utc)
        warnings = config.setdefault("warnings", {})
        key = f"{group_id}:{user_id}"
        window_start = now - timedelta(hours=int(moderation.get("window_hours", 24)))
        existing = [
            item
            for item in warnings.get(key, [])
            if datetime.fromisoformat(item["time"]) >= window_start
        ]
        existing.append({"word": word, "time": now.isoformat()})
        warnings[key] = existing
        self.store.save(config)

        strike_limit = int(moderation.get("strike_limit", 2))
        strikes = len(existing)
        if strikes >= strike_limit and moderation.get("kick_enabled", True):
            return ModerationResult(
                "kick",
                word,
                strikes,
                f"检测到违禁词“{word}”，24 小时内已警告 {strikes} 次，将移出本群。",
            )

        return ModerationResult(
            "warn",
            word,
            strikes,
            f"检测到违禁词“{word}”，这是 24 小时内第 {strikes} 次警告。",
        )

    def _matched_word(self, text: str, banned_words: list[str]) -> str:
        normalized = text.lower()
        for word in banned_words:
            clean_word = str(word).strip()
            if clean_word and clean_word.lower() in normalized:
                return clean_word
        return ""
