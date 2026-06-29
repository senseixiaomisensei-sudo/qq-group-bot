import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

from bot.settings import get_settings


settings = get_settings()

nonebot.init(
    driver="~fastapi+~websockets",
    host=settings.onebot_host,
    port=settings.onebot_port,
)

driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

nonebot.load_plugins("plugins")


if __name__ == "__main__":
    nonebot.run()
