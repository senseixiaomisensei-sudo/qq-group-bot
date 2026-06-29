from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from bot.paths import PROJECT_ROOT
from bot.process_control import (
    NAPCAT_ROOT,
    QQNT_ROOT,
    build_napcat_command,
    build_python_command,
    cleanup_qqnt_intrusive_files,
    is_local_port_established,
    is_port_listening,
    start_hidden,
    terminate_process,
)


LOG_DIR = PROJECT_ROOT / "logs"


class BotControlPanel(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("QQ 群机器人控制台")
        self.geometry("680x460")
        self.resizable(False, False)
        self.events: queue.Queue[str] = queue.Queue()
        self.nonebot_process = None
        self.admin_process = None
        self.napcat_process = None
        self._build_ui()
        self.after(1000, self.refresh_status)
        self.after(300, self.drain_events)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(frame, text="QQ 群管理机器人", font=("Microsoft YaHei UI", 16, "bold"))
        title.pack(anchor="w")

        self.status_var = tk.StringVar(value="正在检测...")
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(8, 16))

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)

        ttk.Button(buttons, text="启动机器人服务", command=self.start_bot_services).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(buttons, text="启动管理后台", command=self.start_admin).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(buttons, text="启动 NapCat QQ", command=self.start_napcat).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(buttons, text="全部启动", command=self.start_all).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(buttons, text="停止本面板启动的服务", command=self.stop_owned).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(buttons, text="清理 QQNT 目录残留", command=self.cleanup_qqnt).grid(row=1, column=1, padx=4, pady=4)
        ttk.Button(buttons, text="打开配置文件", command=self.open_env_file).grid(row=1, column=2, padx=4, pady=4)
        ttk.Button(buttons, text="刷新状态", command=self.refresh_status).grid(row=1, column=3, padx=4, pady=4)

        self.log = tk.Text(frame, height=18, width=88, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        self.write_log("提示：先填写 .env.local 里的 BOT_QQ 和 AGNES_API_KEY，再启动 NapCat QQ。")
        self.write_log("NapCat 会从 D:\\napcat\\NapCat.*.Shell 启动，本控制台不会修改 QQ 安装目录。")

    def write_log(self, message: str) -> None:
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, message + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def drain_events(self) -> None:
        while True:
            try:
                self.write_log(self.events.get_nowait())
            except queue.Empty:
                break
        self.after(300, self.drain_events)

    def refresh_status(self) -> None:
        onebot = "已监听" if is_port_listening(18080) else "未监听"
        napcat_ws = "已连接" if is_local_port_established(18080) else "未连接"
        admin = "已监听" if is_port_listening(8090) else "未监听"
        api = "已填" if self._env_has_value("AGNES_API_KEY") else "未填"
        bot_qq = self._env_value("BOT_QQ") or "未填"
        self.status_var.set(
            f"OneBot 18080：{onebot}    NapCat WS：{napcat_ws}    后台 8090：{admin}    "
            f"BOT_QQ：{bot_qq}    API Key：{api}"
        )
        self.after(3000, self.refresh_status)

    def start_bot_services(self) -> None:
        if is_port_listening(18080):
            self.write_log("NoneBot 已在 127.0.0.1:18080 监听。")
            return
        command = build_python_command(PROJECT_ROOT / "main.py")
        self.nonebot_process = start_hidden(command, LOG_DIR / "nonebot.gui.out.log", LOG_DIR / "nonebot.gui.err.log")
        self.write_log("已隐藏启动 NoneBot。")

    def start_admin(self) -> None:
        if is_port_listening(8090):
            self.write_log("管理后台已在 127.0.0.1:8090 监听。")
            return
        command = build_python_command(PROJECT_ROOT / "admin.py")
        self.admin_process = start_hidden(command, LOG_DIR / "admin.gui.out.log", LOG_DIR / "admin.gui.err.log")
        self.write_log("已隐藏启动管理后台。")

    def start_napcat(self) -> None:
        bot_qq = self._env_value("BOT_QQ")
        command = build_napcat_command(NAPCAT_ROOT, bot_qq)
        if not command.args:
            messagebox.showerror(
                "NapCat 未找到",
                "没有找到 D:\\napcat\\NapCatWinBootMain.exe 或 D:\\napcat\\NapCat.*.Shell\\QQ.exe。",
            )
            return
        self.napcat_process = start_hidden(command, LOG_DIR / "napcat.gui.out.log", LOG_DIR / "napcat.gui.err.log")
        self.write_log(f"已从 {command.cwd} 启动 NapCat QQ。账号参数：{bot_qq or '未设置'}")

    def start_all(self) -> None:
        self.start_bot_services()
        self.start_admin()
        self.start_napcat()

    def stop_owned(self) -> None:
        terminate_process(self.nonebot_process)
        terminate_process(self.admin_process)
        terminate_process(self.napcat_process)
        self.write_log("已停止本面板启动且仍可控的进程。")

    def cleanup_qqnt(self) -> None:
        def worker() -> None:
            removed = cleanup_qqnt_intrusive_files(QQNT_ROOT)
            if removed:
                self.events.put("已清理 QQNT 目录残留：")
                for path in removed:
                    self.events.put(f"  - {path}")
            else:
                self.events.put("QQNT 目录没有发现需要清理的 NapCat 残留。")

        threading.Thread(target=worker, daemon=True).start()

    def open_env_file(self) -> None:
        env_path = PROJECT_ROOT / ".env.local"
        env_path.touch(exist_ok=True)
        import os

        os.startfile(str(env_path))

    def _env_has_value(self, name: str) -> bool:
        return bool(self._env_value(name))

    def _env_value(self, name: str) -> str:
        env_path = PROJECT_ROOT / ".env.local"
        if not env_path.exists():
            return ""
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip()
        return ""


if __name__ == "__main__":
    BotControlPanel().mainloop()
