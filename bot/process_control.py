from __future__ import annotations

import os
import signal
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from bot.paths import PROJECT_ROOT
from bot.settings import get_settings


NAPCAT_ROOT = Path("D:/napcat")
QQNT_ROOT = Path("C:/Program Files/Tencent/QQNT")
QQNT_INTRUSIVE_FILENAMES = {"NapCatWinBootMain.exe", "NapCatWinBootHook.dll"}
CREATE_NO_WINDOW = 0x08000000


@dataclass(frozen=True)
class CommandSpec:
    args: list[str]
    cwd: Path


def build_python_command(module_file: Path) -> CommandSpec:
    return CommandSpec([sys.executable, str(module_file)], PROJECT_ROOT)


def resolve_napcat_shell_root(napcat_root: Path = NAPCAT_ROOT) -> Path | None:
    shells = sorted(
        [path for path in napcat_root.glob("NapCat.*.Shell") if (path / "QQ.exe").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if shells:
        return shells[0]
    return None


def resolve_napcat_boot(napcat_root: Path = NAPCAT_ROOT) -> Path | None:
    shell_root = resolve_napcat_shell_root(napcat_root)
    if shell_root:
        shell_boot = shell_root / "NapCatWinBootMain.exe"
        if shell_boot.exists():
            return shell_boot
    for boot in (
        napcat_root / "NapCatWinBootMain.exe",
        napcat_root / "bootmain" / "NapCatWinBootMain.exe",
    ):
        if boot.exists():
            return boot
    return None


def prepare_napcat_shell_bootstrap(napcat_root: Path = NAPCAT_ROOT) -> Path | None:
    shell_root = resolve_napcat_shell_root(napcat_root)
    if not shell_root:
        return None

    for filename in ("NapCatWinBootMain.exe", "NapCatWinBootHook.dll"):
        destination = shell_root / filename
        if destination.exists():
            continue

        source = None
        for candidate in (napcat_root / filename, napcat_root / "bootmain" / filename):
            if candidate.exists():
                source = candidate
                break
        if not source:
            return None
        shutil.copy2(source, destination)

    sync_napcat_config_to_shell(napcat_root, shell_root)
    return shell_root / "NapCatWinBootMain.exe"


def sync_napcat_config_to_shell(napcat_root: Path = NAPCAT_ROOT, shell_root: Path | None = None) -> list[Path]:
    shell_root = shell_root or resolve_napcat_shell_root(napcat_root)
    source_dir = napcat_root / "config"
    if not shell_root or not source_dir.exists():
        return []

    target_dir = shell_root / "config"
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for source in source_dir.glob("onebot11*.json"):
        destination = target_dir / source.name
        shutil.copy2(source, destination)
        copied.append(destination)
    return copied


def build_napcat_command(napcat_root: Path = NAPCAT_ROOT, bot_qq: str = "") -> CommandSpec:
    shell_root = resolve_napcat_shell_root(napcat_root)
    boot = prepare_napcat_shell_bootstrap(napcat_root)
    if not boot or not shell_root:
        return CommandSpec([], napcat_root)
    args = [str(boot)]
    if bot_qq:
        args.append(bot_qq)
    return CommandSpec(args, shell_root)


def start_hidden(command: CommandSpec, stdout_path: Path, stderr_path: Path) -> subprocess.Popen | None:
    if not command.args:
        return None
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("ab")
    stderr = stderr_path.open("ab")
    return subprocess.Popen(
        command.args,
        cwd=str(command.cwd),
        stdout=stdout,
        stderr=stderr,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
    )


def terminate_process(process: subprocess.Popen | None) -> None:
    if process and process.poll() is None:
        process.terminate()


def is_port_listening(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def is_local_port_established(port: int) -> bool:
    try:
        import psutil  # type: ignore
    except Exception:
        return False

    for conn in psutil.net_connections(kind="tcp"):
        if conn.status != "ESTABLISHED":
            continue
        local_port = getattr(conn.laddr, "port", None)
        remote_port = getattr(conn.raddr, "port", None) if conn.raddr else None
        if local_port == port or remote_port == port:
            return True
    return False


def qqnt_cleanup_targets(qqnt_root: Path = QQNT_ROOT) -> list[Path]:
    targets: list[Path] = []
    for name in QQNT_INTRUSIVE_FILENAMES:
        path = qqnt_root / name
        if path.exists():
            targets.append(path)
    config_dir = qqnt_root / "config"
    if config_dir.exists():
        targets.extend(config_dir.glob("onebot11*.json"))
    return targets


def cleanup_qqnt_intrusive_files(qqnt_root: Path = QQNT_ROOT) -> list[Path]:
    removed: list[Path] = []
    for path in qqnt_cleanup_targets(qqnt_root):
        try:
            path.unlink()
            removed.append(path)
        except FileNotFoundError:
            pass
    config_dir = qqnt_root / "config"
    if config_dir.exists():
        try:
            next(config_dir.iterdir())
        except StopIteration:
            config_dir.rmdir()
    return removed


def stop_processes_by_name(names: set[str]) -> None:
    if os.name != "nt":
        return
    try:
        import psutil  # type: ignore
    except Exception:
        return
    for proc in psutil.process_iter(["name", "exe"]):
        if str(proc.info.get("name", "")).lower() in names:
            try:
                proc.send_signal(signal.SIGTERM)
            except Exception:
                pass


def current_bot_qq() -> str:
    return get_settings().bot_qq.strip()
