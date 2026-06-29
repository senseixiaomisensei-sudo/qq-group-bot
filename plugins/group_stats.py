from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.rule import to_me

from bot.config_store import ConfigStore
from bot.onebot_helpers import plain_text
from bot.paths import CONFIG_PATH
from bot.stats import GroupStatsService


stats_matcher = on_message(rule=to_me(), priority=10, block=False)


@stats_matcher.handle()
async def handle_stats(bot: Bot, event: GroupMessageEvent) -> None:
    text = plain_text(event)
    if not text.startswith("群统计"):
        return
    summary = GroupStatsService(ConfigStore(CONFIG_PATH)).summary(str(event.group_id))
    await bot.send(
        event,
        (
            "本群统计：\n"
            f"消息数：{summary['message_count']}\n"
            f"活跃成员：{summary['active_user_count']}\n"
            f"入群记录：{summary['joins']}\n"
            f"退群记录：{summary['leaves']}"
        ),
    )
