from pathlib import Path

from bot.process_control import (
    QQNT_INTRUSIVE_FILENAMES,
    build_napcat_command,
    is_local_port_established,
    prepare_napcat_shell_bootstrap,
    qqnt_cleanup_targets,
    resolve_napcat_shell_root,
    sync_napcat_config_to_shell,
)


def test_napcat_command_uses_isolated_shell_root(tmp_path):
    napcat_root = tmp_path / "napcat"
    napcat_root.mkdir()
    boot = napcat_root / "NapCatWinBootMain.exe"
    boot.write_bytes(b"")
    hook = napcat_root / "NapCatWinBootHook.dll"
    hook.write_bytes(b"")
    shell_root = napcat_root / "NapCat.44498.Shell"
    shell_root.mkdir()
    (shell_root / "QQ.exe").write_bytes(b"")

    command = build_napcat_command(napcat_root, "123456")

    assert command.cwd == shell_root
    assert command.args == [str(shell_root / "NapCatWinBootMain.exe"), "123456"]
    assert (shell_root / "NapCatWinBootMain.exe").exists()
    assert (shell_root / "NapCatWinBootHook.dll").exists()


def test_napcat_command_requires_shell_qq(tmp_path):
    napcat_root = tmp_path / "napcat"
    napcat_root.mkdir()
    (napcat_root / "NapCatWinBootMain.exe").write_bytes(b"")

    command = build_napcat_command(napcat_root, "")

    assert "Program Files" not in str(command.cwd)
    assert command.args == []


def test_resolve_napcat_shell_root_prefers_shell_directory(tmp_path):
    napcat_root = tmp_path / "napcat"
    napcat_root.mkdir()
    installer = napcat_root / "QQ.exe"
    installer.write_bytes(b"installer")
    shell_root = napcat_root / "NapCat.44498.Shell"
    shell_root.mkdir()
    (shell_root / "QQ.exe").write_bytes(b"real shell")

    assert resolve_napcat_shell_root(napcat_root) == shell_root


def test_prepare_napcat_shell_bootstrap_returns_none_without_hook(tmp_path):
    napcat_root = tmp_path / "napcat"
    napcat_root.mkdir()
    (napcat_root / "NapCatWinBootMain.exe").write_bytes(b"")
    shell_root = napcat_root / "NapCat.44498.Shell"
    shell_root.mkdir()
    (shell_root / "QQ.exe").write_bytes(b"")

    assert prepare_napcat_shell_bootstrap(napcat_root) is None


def test_sync_napcat_config_to_shell_copies_onebot_configs(tmp_path):
    napcat_root = tmp_path / "napcat"
    config_dir = napcat_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "onebot11.json").write_text('{"ok": true}', encoding="utf-8")
    (config_dir / "ignored.txt").write_text("x", encoding="utf-8")
    shell_root = napcat_root / "NapCat.44498.Shell"
    shell_root.mkdir()
    (shell_root / "QQ.exe").write_bytes(b"")

    copied = sync_napcat_config_to_shell(napcat_root)

    assert copied == [shell_root / "config" / "onebot11.json"]
    assert (shell_root / "config" / "onebot11.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert not (shell_root / "config" / "ignored.txt").exists()


def test_is_local_port_established_returns_bool():
    assert isinstance(is_local_port_established(9), bool)


def test_qqnt_cleanup_only_targets_napcat_artifacts(tmp_path):
    qqnt_root = tmp_path / "QQNT"
    config_dir = qqnt_root / "config"
    config_dir.mkdir(parents=True)
    for name in QQNT_INTRUSIVE_FILENAMES:
        (qqnt_root / name).write_text("x", encoding="utf-8")
    (config_dir / "onebot11.json").write_text("{}", encoding="utf-8")
    (config_dir / "onebot11_123.json").write_text("{}", encoding="utf-8")
    (qqnt_root / "QQ.exe").write_text("do not touch", encoding="utf-8")

    targets = qqnt_cleanup_targets(qqnt_root)

    target_names = {path.name for path in targets}
    assert QQNT_INTRUSIVE_FILENAMES <= target_names
    assert "onebot11.json" in target_names
    assert "onebot11_123.json" in target_names
    assert "QQ.exe" not in target_names
