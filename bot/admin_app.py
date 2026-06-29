from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from bot.cloud_runtime import RuntimeManager, default_runtime, mask_secret
from bot.config_store import ConfigStore
from bot.settings import get_settings


class KeywordsPayload(BaseModel):
    items: dict[str, str] = Field(default_factory=dict)


class WordsPayload(BaseModel):
    items: list[str] = Field(default_factory=list)


class WelcomePayload(BaseModel):
    enabled: bool = True
    message: str


class AccountPayload(BaseModel):
    qq: str


class ConfigPayload(BaseModel):
    features: dict[str, bool] | None = None
    welcome: WelcomePayload | None = None
    banned_words: list[str] | None = None
    keywords: dict[str, str] | None = None


class ApiConfigPayload(BaseModel):
    base_url: str | None = None
    api_key: str | None = None


def create_admin_app(store: ConfigStore, runtime: RuntimeManager | None = None) -> FastAPI:
    settings = get_settings()
    runtime = runtime or default_runtime(store)
    app = FastAPI(title="QQ Group Bot Admin", version="2.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
        if settings.admin_token and x_admin_token != settings.admin_token:
            raise HTTPException(status_code=401, detail="控制台密钥不正确。")

    write_guard = Depends(require_admin)

    @app.get("/health")
    def health() -> dict[str, Any]:
        current = get_settings()
        return {
            "status": "ok",
            "version": app.version,
            "bind": current.admin_host,
            "port": current.admin_port,
            "ai_configured": bool(current.agnes_api_key),
            "bot_state": runtime.state(),
        }

    @app.get("/status")
    def status() -> dict[str, Any]:
        return runtime.state()

    @app.post("/bot/account", dependencies=[write_guard])
    def save_account(payload: AccountPayload) -> dict[str, Any]:
        try:
            return runtime.save_account(payload.qq)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.post("/bot/login/start", dependencies=[write_guard])
    def start_login() -> dict[str, Any]:
        return runtime.start_login()

    @app.post("/bot/hosting/start", dependencies=[write_guard])
    def start_hosting() -> dict[str, Any]:
        return runtime.start_hosting()

    @app.post("/bot/hosting/stop", dependencies=[write_guard])
    def stop_hosting() -> dict[str, Any]:
        return runtime.stop_hosting()

    @app.get("/config")
    def get_config() -> dict[str, Any]:
        config = store.load()
        return _public_config(config)

    @app.post("/config", dependencies=[write_guard])
    def update_config(payload: ConfigPayload) -> dict[str, Any]:
        config = store.load()
        if payload.features is not None:
            config["features"].update({key: bool(value) for key, value in payload.features.items()})
            config["welcome"]["enabled"] = bool(config["features"].get("welcome", True))
            config["moderation"]["enabled"] = bool(config["features"].get("banned_words", True))
        if payload.welcome is not None:
            config["welcome"] = payload.welcome.model_dump()
            config["features"]["welcome"] = payload.welcome.enabled
        if payload.banned_words is not None:
            config["banned_words"] = [str(item).strip() for item in payload.banned_words if str(item).strip()]
        if payload.keywords is not None:
            config["keywords"] = {str(key).strip(): str(value) for key, value in payload.keywords.items() if str(key).strip()}
        store.save(config)
        return _public_config(config)

    @app.get("/logs")
    def logs(limit: int = 100) -> dict[str, list[str]]:
        return {"items": runtime.recent_logs(limit)}

    @app.get("/qr-code", response_model=None)
    def qr_code():
        path = runtime.latest_qr_code()
        if not path:
            return Response(status_code=404)
        return FileResponse(path, media_type="image/png")

    @app.get("/api-status")
    def api_status() -> dict[str, Any]:
        current = get_settings()
        return {
            "configured": bool(current.agnes_api_key),
            "base_url": current.agnes_base_url,
            "key_preview": mask_secret(current.agnes_api_key),
            "models": {
                "chat": current.agnes_text_model,
                "image": current.agnes_image_model,
                "video": current.agnes_video_model,
            },
        }

    @app.post("/api-config", dependencies=[write_guard])
    def api_config(payload: ApiConfigPayload) -> dict[str, Any]:
        runtime.log("API 配置更新请求已收到。Railway 环境变量仍是推荐的密钥保存方式。")
        return {
            "accepted": bool(payload.base_url or payload.api_key),
            "message": "请在 Railway 后端变量中保存 API 密钥，静态网页不会保存完整密钥。",
        }

    @app.get("/stats/groups")
    def group_stats() -> dict[str, Any]:
        return {"groups": store.load()["stats"]["groups"]}

    @app.get("/config/keywords")
    def get_keywords() -> dict[str, Any]:
        return {"items": store.load()["keywords"]}

    @app.post("/config/keywords", dependencies=[write_guard])
    def set_keywords(payload: KeywordsPayload) -> dict[str, Any]:
        config = store.load()
        config["keywords"] = payload.items
        store.save(config)
        return {"items": payload.items}

    @app.get("/config/banned-words")
    def get_banned_words() -> dict[str, Any]:
        return {"items": store.load()["banned_words"]}

    @app.post("/config/banned-words", dependencies=[write_guard])
    def set_banned_words(payload: WordsPayload) -> dict[str, Any]:
        config = store.load()
        config["banned_words"] = payload.items
        store.save(config)
        return {"items": payload.items}

    @app.get("/config/welcome")
    def get_welcome() -> dict[str, Any]:
        return store.load()["welcome"]

    @app.post("/config/welcome", dependencies=[write_guard])
    def set_welcome(payload: WelcomePayload) -> dict[str, Any]:
        config = store.load()
        config["welcome"] = payload.model_dump()
        config["features"]["welcome"] = payload.enabled
        store.save(config)
        return config["welcome"]

    return app


def _public_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "features": config["features"],
        "welcome": config["welcome"],
        "banned_words": config["banned_words"],
        "keywords": config["keywords"],
        "bot": config["bot"],
    }
