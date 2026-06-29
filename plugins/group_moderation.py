from nonebot import on_notice, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, GroupMessageEvent

from bot.config_store import ConfigStore
from bot.moderation import ModerationService
from bot.paths import CONFIG_PATH
from bot.stats import GroupStatsService


store = ConfigStore(CONFIG_PATH)
moderation = ModerationService(store)
stats = GroupStatsService(store)

message_matcher = on_message(priority=1, block=False)
join_matcher = on_notice(priority=1, block=False)


@message_matcher.handle()
async def handle_group_message(bot: Bot, event: GroupMessageEvent) -> None:
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    stats.record_message(group_id, user_id)

    text = event.get_plaintext().strip()
    config = store.load()
    features = config.get("features", {})
    if features.get("keyword_replies", True):
        for keyword, reply in config.get("keywords", {}).items():
            if keyword and keyword in text:
                await bot.send(event, reply)
                break

    if not features.get("banned_words", True):
        return

    result = moderation.check_message(group_id, user_id, text)
    if result.action == "warn":
        await bot.send(event, result.message)
    elif result.action == "kick":
        await bot.send(event, result.message)
        await bot.set_group_kick(group_id=int(group_id), user_id=int(user_id), reject_add_request=False)


@join_matcher.handle()
async def handle_group_join(bot: Bot, event: GroupIncreaseNoticeEvent) -> None:
    group_id = str(event.group_id)
    user_id = str(event.user_id)
    stats.record_join(group_id, user_id)
    config = store.load()
    if not config.get("features", {}).get("welcome", True):
        return
    welcome = config["welcome"]
    if not welcome.get("enabled", True):
        return
    nickname = str(user_id)
    message = welcome.get("message", "").format(nickname=nickname, user_id=user_id, group_id=group_id)
    if message:
        await bot.send(event, message)
