from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections import deque
from pathlib import Path
from threading import RLock
from typing import Any

from bot.config_store import ConfigStore
from bot.settings import get_settings


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)(password|passwd|pwd|api[_-]?key|authorization|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)Bearer\s+\S+"),
]


LOGIN_MESSAGES = {
    "not_configured": "请先填写机器人 QQ 号。",
    "configured": "机器人账号已保存，点击开始托管后进入扫码/快速登录。",
    "waiting_qr": "等待扫码或快速登录确认。",
    "waiting_verification": "需要你本人完成验证码、滑块或设备锁。",
    "online": "机器人在线。",
    "reconnecting": "正在自动重连。",
    "failed": "启动失败，请查看日志。",
    "needs_manual_action": "需要你本人完成 QQ 官方验证后再继续。",
}


def sanitize_log_text(text: str) -> str:
    redacted = str(text)
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[redacted]", redacted)
    return redacted


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-4:]}"


def build_lagrange_appsettings(bot_qq: str, host: str, port: int) -> dict[str, Any]:
    uin = int(str(bot_qq).strip() or 0)
    return {
        "$schema": "https://raw.githubusercontent.com/LagrangeDev/Lagrange.Core/master/Lagrange.OneBot/Resources/appsettings_schema.json",
        "Logging": {
            "LogLevel": {
                "Default": "Information",
                "Microsoft": "Warning",
                "Microsoft.Hosting.Lifetime": "Information",
            }
        },
        "SignServerUrl": "",
        "SignProxyUrl": "",
        "MusicSignServerUrl": "",
        "Account": {
            "Uin": uin,
            "Protocol": "Linux",
            "AutoReconnect": True,
            "AutoReLogin": True,
            "GetOptimumServer": True,
        },
        "Message": {
            "IgnoreSelf": True,
            "StringPost": False,
        },
        "QrCode": {
            "ConsoleCompatibilityMode": False,
        },
        "Implementations": [
            {
                "Type": "ReverseWebSocket",
                "Host": host,
                "Port": int(port),
                "Suffix": "/onebot/v11/ws",
                "ReconnectInterval": 5000,
                "HeartBeatInterval": 5000,
                "HeartBeatEnable": True,
                "AccessToken": "",
            }
        ],
    }


class RuntimeManager:
    def __init__(
        self,
        store: ConfigStore,
        *,
        data_dir: str | Path | None = None,
        lagrange_bin: str | Path | None = None,
        spawn_enabled: bool = True,
    ):
        settings = get_settings()
        self.store = store
        self.data_dir = Path(data_dir or settings.lagrange_data_dir)
        self.lagrange_bin = Path(lagrange_bin or settings.lagrange_bin)
        self.spawn_enabled = spawn_enabled
        self.logs: deque[str] = deque(maxlen=300)
        self._lock = RLock()
        self._lagrange_process: subprocess.Popen | None = None
        self._nonebot_process: subprocess.Popen | None = None

    def save_account(self, qq: str) -> dict[str, Any]:
        clean_qq = self._clean_qq(qq)
        config = self.store.load()
        config["bot"].update(
            {
                "qq": clean_qq,
                "login_state": "configured" if clean_qq else "not_configured",
                "manual_action": LOGIN_MESSAGES["configured"] if clean_qq else LOGIN_MESSAGES["not_configured"],
            }
        )
        self.store.save(config)
        if clean_qq:
            self.write_lagrange_config(clean_qq)
            self.log(f"机器人 QQ 已保存：{clean_qq}")
        return self.state()

    def write_lagrange_config(self, qq: str) -> Path:
        settings = get_settings()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / "appsettings.json"
        config = build_lagrange_appsettings(qq, settings.onebot_host, settings.onebot_port)
        path.write_text(json.dumps(config, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
        return path

    def start_login(self) -> dict[str, Any]:
        return self.start_hosting()

    def start_hosting(self) -> dict[str, Any]:
        with self._lock:
            config = self.store.load()
            qq = config["bot"].get("qq", "").strip()
            if not qq:
                config["bot"].update(
                    {
                        "hosting_enabled": False,
                        "login_state": "not_configured",
                        "manual_action": LOGIN_MESSAGES["not_configured"],
                    }
                )
                self.store.save(config)
                return self.state()

            self.write_lagrange_config(qq)
            config["bot"]["hosting_enabled"] = True
            config["bot"]["login_state"] = "waiting_qr"
            config["bot"]["manual_action"] = LOGIN_MESSAGES["waiting_qr"]
            self.store.save(config)
            self.log("开始托管，等待扫码或快速登录确认。")

            if self.spawn_enabled:
                self._start_processes()
            return self.state()

    def stop_hosting(self) -> dict[str, Any]:
        with self._lock:
            self._terminate(self._lagrange_process)
            self._terminate(self._nonebot_process)
            self._lagrange_process = None
            self._nonebot_process = None
            config = self.store.load()
            config["bot"]["hosting_enabled"] = False
            config["bot"]["login_state"] = "configured" if config["bot"].get("qq") else "not_configured"
            config["bot"]["manual_action"] = LOGIN_MESSAGES[config["bot"]["login_state"]]
            self.store.save(config)
            self.log("已停止托管。")
            return self.state()

    def state(self) -> dict[str, Any]:
        config = self.store.load()
        bot = config["bot"]
        qr_code = self.latest_qr_code()
        groups = config.get("stats", {}).get("groups", {})
        message_count = sum(int(group.get("message_count", 0)) for group in groups.values())
        lagrange_running = self._is_running(self._lagrange_process)
        nonebot_running = self._is_running(self._nonebot_process)
        login_state = bot.get("login_state", "not_configured")
        if bot.get("hosting_enabled") and lagrange_running and nonebot_running:
            login_state = "online"
        return {
            "qq": bot.get("qq", ""),
            "hosting_enabled": bool(bot.get("hosting_enabled", False)),
            "login_state": login_state,
            "online": login_state == "online",
            "manual_action": bot.get("manual_action") or LOGIN_MESSAGES.get(login_state, ""),
            "group_count": len(groups),
            "message_count": message_count,
            "lagrange_running": lagrange_running,
            "nonebot_running": nonebot_running,
            "qr_available": qr_code is not None,
            "qr_code_url": f"/qr-code?ts={int(qr_code.stat().st_mtime)}" if qr_code else "",
            "persistence_path": str(self.data_dir),
        }

    def log(self, text: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"{timestamp} {sanitize_log_text(text)}")

    def recent_logs(self, limit: int = 100) -> list[str]:
        file_logs = self._tail_log_file(self.data_dir / "runtime.log", limit)
        file_logs.extend(self._tail_log_file(self.data_dir / "lagrange.log", limit))
        combined = list(self.logs) + [sanitize_log_text(item) for item in file_logs]
        return combined[-limit:]

    def latest_qr_code(self) -> Path | None:
        if not self.data_dir.exists():
            return None
        candidates = sorted(self.data_dir.glob("qr-*.png"), key=lambda path: path.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None

    def _start_processes(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        runtime_log = (self.data_dir / "runtime.log").open("ab")
        lagrange_log = (self.data_dir / "lagrange.log").open("ab")
        if not self._is_running(self._nonebot_process):
            self._nonebot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=Path(__file__).resolve().parent.parent,
                stdout=runtime_log,
                stderr=subprocess.STDOUT,
            )
        if not self.lagrange_bin.exists():
            config = self.store.load()
            config["bot"]["login_state"] = "needs_manual_action"
            config["bot"]["manual_action"] = "Lagrange 可执行文件未找到，请确认 Railway 镜像包含 /app/bin/Lagrange.OneBot。"
            self.store.save(config)
            self.log(config["bot"]["manual_action"])
            return
        if not self._is_running(self._lagrange_process):
            self._lagrange_process = subprocess.Popen(
                [str(self.lagrange_bin)],
                cwd=str(self.data_dir),
                stdout=lagrange_log,
                stderr=subprocess.STDOUT,
            )

    def _clean_qq(self, qq: str) -> str:
        value = str(qq).strip()
        if not value.isdigit():
            raise ValueError("QQ 号只允许填写数字。")
        return value

    def _is_running(self, process: subprocess.Popen | None) -> bool:
        return bool(process and process.poll() is None)

    def _terminate(self, process: subprocess.Popen | None) -> None:
        if process and process.poll() is None:
            process.terminate()

    def _tail_log_file(self, path: Path, limit: int) -> list[str]:
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []
        return lines[-limit:]


def default_runtime(store: ConfigStore) -> RuntimeManager:
    return RuntimeManager(store, spawn_enabled=os.getenv("BOT_SPAWN_ENABLED", "1") != "0")
