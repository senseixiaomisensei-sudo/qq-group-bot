from dataclasses import dataclass
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from bot.paths import PROJECT_ROOT


load_dotenv(PROJECT_ROOT / ".env.local")


@dataclass(frozen=True)
class Settings:
    bot_qq: str
    agnes_api_key: str
    agnes_base_url: str
    agnes_text_model: str
    agnes_fallback_text_model: str
    agnes_image_model: str
    agnes_video_model: str
    onebot_host: str
    onebot_port: int
    admin_host: str
    admin_port: int
    admin_token: str
    cors_origins: tuple[str, ...]
    lagrange_data_dir: str
    lagrange_bin: str


def _int_env(name: str, default: int) -> int:
    value = getenv(name)
    if not value:
        return default
    return int(value)


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    value = getenv(name, default)
    return tuple(item.strip() for item in value.split(",") if item.strip())


def get_settings() -> Settings:
    return Settings(
        bot_qq=getenv("BOT_QQ", ""),
        agnes_api_key=getenv("AGNES_API_KEY", ""),
        agnes_base_url=getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"),
        agnes_text_model=getenv("AGNES_TEXT_MODEL", "agnes-2.0-flash"),
        agnes_fallback_text_model=getenv("AGNES_FALLBACK_TEXT_MODEL", "agnes-1.5-flash"),
        agnes_image_model=getenv("AGNES_IMAGE_MODEL", "agnes-image-2.1-flash"),
        agnes_video_model=getenv("AGNES_VIDEO_MODEL", "agnes-video-v2.0"),
        onebot_host=getenv("ONEBOT_HOST", "127.0.0.1"),
        onebot_port=_int_env("ONEBOT_PORT", 18080),
        admin_host=getenv("ADMIN_HOST", "127.0.0.1"),
        admin_port=_int_env("PORT", _int_env("ADMIN_PORT", 8090)),
        admin_token=getenv("ADMIN_TOKEN", ""),
        cors_origins=_csv_env("CORS_ORIGINS", "*"),
        lagrange_data_dir=getenv("LAGRANGE_DATA_DIR", str(PROJECT_ROOT / "data" / "lagrange")),
        lagrange_bin=getenv("LAGRANGE_BIN", "/app/bin/Lagrange.OneBot"),
    )


def env_file_path() -> Path:
    return PROJECT_ROOT / ".env.local"
