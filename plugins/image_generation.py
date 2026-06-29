from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import to_me

from bot.ai_client import AgnesClient
from bot.config_store import ConfigStore
from bot.onebot_helpers import plain_text, send_asset
from bot.paths import CONFIG_PATH


image_gen_matcher = on_message(rule=to_me(), priority=10, block=False)
store = ConfigStore(CONFIG_PATH)


IMAGE_PREFIXES = ("生成图片", "画一个", "画个", "画")


def extract_image_prompt(text: str) -> str:
    clean_text = text.strip()
    for prefix in IMAGE_PREFIXES:
        if clean_text.startswith(prefix):
            return clean_text.removeprefix(prefix).strip()
    return ""


@image_gen_matcher.handle()
async def handle_image_generation(bot: Bot, event: GroupMessageEvent) -> None:
    if not store.load().get("features", {}).get("ai_image", True):
        return

    text = plain_text(event)
    prompt = extract_image_prompt(text)
    if not prompt:
        return

    asset = await AgnesClient().generate_image(prompt)
    if asset.raw.get("error"):
        await bot.send(event, "AI API key 未配置，请先在控制台确认 API 状态。")
        return
    await send_asset(bot, event, "图片生成结果：", asset.url)
