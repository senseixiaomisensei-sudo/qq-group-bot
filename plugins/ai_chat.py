from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import to_me

from bot.ai_client import AgnesClient
from bot.config_store import ConfigStore
from bot.onebot_helpers import plain_text
from bot.paths import CONFIG_PATH


chat_matcher = on_message(rule=to_me(), priority=20, block=False)
store = ConfigStore(CONFIG_PATH)


@chat_matcher.handle()
async def handle_chat(bot: Bot, event: GroupMessageEvent) -> None:
    if not store.load().get("features", {}).get("ai_chat", True):
        return
    text = plain_text(event)
    if not text or text.startswith(("看看这张图", "生成图片", "生成视频", "群统计")):
        return
    if text.startswith("聊聊天"):
        text = text.removeprefix("聊聊天").strip()
    if not text:
        text = "陪大家随便聊两句。"
    reply = await AgnesClient().chat(text)
    await bot.send(event, reply)
