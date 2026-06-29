from bot.admin_app import create_admin_app
from bot.config_store import ConfigStore
from bot.paths import CONFIG_PATH


app = create_admin_app(ConfigStore(CONFIG_PATH))
