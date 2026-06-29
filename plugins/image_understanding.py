from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import to_me

from bot.ai_client import AgnesClient
from bot.config_store import ConfigStore
from bot.onebot_helpers import first_image_url, plain_text
from bot.paths import CONFIG_PATH


image_matcher = on_message(rule=to_me(), priority=10, block=False)
store = ConfigStore(CONFIG_PATH)


@image_matcher.handle()
async def handle_image(bot: Bot, event: GroupMessageEvent) -> None:
    if not store.load().get("features", {}).get("ai_chat", True):
        return
    text = plain_text(event)
    if not text.startswith("看看这张图"):
        return

    image_url = first_image_url(event)
    if not image_url:
        await bot.send(event, "我没看到图片。请在同一条消息里带上图片再 @我。")
        return

    prompt = text.removeprefix("看看这张图").strip() or "请描述并分析这张图片。"
    reply = await AgnesClient().understand_image(prompt, image_url)
    await bot.send(event, reply)
