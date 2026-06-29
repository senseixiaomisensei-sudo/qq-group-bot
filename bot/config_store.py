import json
import time
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    "features": {
        "welcome": True,
        "keyword_replies": True,
        "banned_words": True,
        "ai_chat": True,
        "ai_image": True,
        "ai_video": True,
    },
    "bot": {
        "qq": "",
        "hosting_enabled": False,
        "login_state": "not_configured",
        "manual_action": "请先填写机器人 QQ 号。"
    },
    "welcome": {
        "enabled": True,
        "message": "欢迎 {nickname} 加入本群！请先看看群公告，祝你聊得开心。",
    },
    "keywords": {},
    "banned_words": [],
    "moderation": {
        "enabled": True,
        "strike_limit": 2,
        "window_hours": 24,
        "kick_enabled": True,
    },
    "warnings": {},
    "stats": {
        "groups": {},
    },
}


class ConfigStore:
    _lock = RLock()

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                config = deepcopy(DEFAULT_CONFIG)
                self.save(config)
                return config

            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            return self._merge_defaults(data)

    def save(self, config: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(config, file, ensure_ascii=False, indent=2)
                file.write("\n")
            self._replace_with_retry(temp_path)

    def update(self, section: str, value: Any) -> dict[str, Any]:
        config = self.load()
        config[section] = value
        self.save(config)
        return config

    def _merge_defaults(self, data: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(DEFAULT_CONFIG)
        for key, value in data.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(value)
            else:
                merged[key] = value
        return merged

    def _replace_with_retry(self, temp_path: Path) -> None:
        last_error: PermissionError | None = None
        for _ in range(10):
            try:
                temp_path.replace(self.path)
                return
            except PermissionError as error:
                last_error = error
                time.sleep(0.05)
        if last_error:
            raise last_error
