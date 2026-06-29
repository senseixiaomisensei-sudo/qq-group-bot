from bot.config_store import ConfigStore


class GroupStatsService:
    def __init__(self, store: ConfigStore):
        self.store = store

    def record_message(self, group_id: str, user_id: str) -> None:
        config = self.store.load()
        group = config["stats"]["groups"].setdefault(
            str(group_id),
            {"message_count": 0, "active_users": {}, "joins": 0, "leaves": 0},
        )
        group["message_count"] += 1
        group["active_users"][str(user_id)] = group["active_users"].get(str(user_id), 0) + 1
        self.store.save(config)

    def record_join(self, group_id: str, user_id: str) -> None:
        config = self.store.load()
        group = config["stats"]["groups"].setdefault(
            str(group_id),
            {"message_count": 0, "active_users": {}, "joins": 0, "leaves": 0},
        )
        group["joins"] += 1
        group["active_users"].setdefault(str(user_id), 0)
        self.store.save(config)

    def record_leave(self, group_id: str, user_id: str) -> None:
        config = self.store.load()
        group = config["stats"]["groups"].setdefault(
            str(group_id),
            {"message_count": 0, "active_users": {}, "joins": 0, "leaves": 0},
        )
        group["leaves"] += 1
        self.store.save(config)

    def summary(self, group_id: str) -> dict[str, int]:
        config = self.store.load()
        group = config["stats"]["groups"].get(str(group_id), {})
        return {
            "message_count": int(group.get("message_count", 0)),
            "active_user_count": len(group.get("active_users", {})),
            "joins": int(group.get("joins", 0)),
            "leaves": int(group.get("leaves", 0)),
        }

    def all_groups(self) -> dict:
        return self.store.load()["stats"]["groups"]
