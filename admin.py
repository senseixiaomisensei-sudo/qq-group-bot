import uvicorn

from bot.admin_app import create_admin_app
from bot.config_store import ConfigStore
from bot.paths import CONFIG_PATH
from bot.settings import get_settings


app = create_admin_app(ConfigStore(CONFIG_PATH))


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(app, host=settings.admin_host, port=settings.admin_port)
