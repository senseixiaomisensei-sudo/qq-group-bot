from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment


def plain_text(event) -> str:
    return event.get_plaintext().strip()


def first_image_url(event) -> str:
    for segment in event.message:
        if segment.type == "image":
            return segment.data.get("url") or segment.data.get("file") or ""
    return ""


async def send_asset(bot: Bot, event, title: str, url: str) -> None:
    if url:
        await bot.send(event, Message([MessageSegment.text(f"{title}\n{url}")]))
    else:
        await bot.send(event, f"{title}\n生成任务已提交，但接口没有返回可直接发送的 URL。")
