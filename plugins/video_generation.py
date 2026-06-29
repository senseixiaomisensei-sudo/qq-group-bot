from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import to_me

from bot.ai_client import AgnesClient
from bot.config_store import ConfigStore
from bot.onebot_helpers import plain_text, send_asset
from bot.paths import CONFIG_PATH


video_gen_matcher = on_message(rule=to_me(), priority=10, block=False)
store = ConfigStore(CONFIG_PATH)


VIDEO_PREFIXES = ("生成视频", "做视频")


def extract_video_prompt(text: str) -> str:
    clean_text = text.strip()
    for prefix in VIDEO_PREFIXES:
        if clean_text.startswith(prefix):
            return clean_text.removeprefix(prefix).strip()
    return ""


@video_gen_matcher.handle()
async def handle_video_generation(bot: Bot, event: GroupMessageEvent) -> None:
    if not store.load().get("features", {}).get("ai_video", True):
        return

    text = plain_text(event)
    prompt = extract_video_prompt(text)
    if not prompt:
        return

    asset = await AgnesClient().generate_video(prompt)
    if asset.raw.get("error"):
        await bot.send(event, "AI API key 未配置，请先在控制台确认 API 状态。")
        return
    await send_asset(bot, event, "视频生成结果：", asset.url)
