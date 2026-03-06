from objects.sprite import Sprite
from pathlib import Path
import json


class Item(Sprite):
    DESPAWN_TIME = 30000
    _ITEM_CONFIG = None

    @staticmethod
    def _load_item_config():
        if Item._ITEM_CONFIG is not None:
            return Item._ITEM_CONFIG

        path = Path.cwd() / "assets" / "items.json"
        if not path.exists():
            Item._ITEM_CONFIG = {}
            return Item._ITEM_CONFIG

        try:
            with open(path, "r") as f:
                Item._ITEM_CONFIG = json.load(f)
        except (OSError, json.JSONDecodeError):
            Item._ITEM_CONFIG = {}

        return Item._ITEM_CONFIG

    @staticmethod
    def sprite_from_item_id(item_id):
        item_config = Item._load_item_config()
        item_data = item_config.get(item_id, {})
        return item_data.get("sprite", f"assets/items/{item_id}.png")

    @staticmethod
    def price_from_item_id(item_id):
        item_config = Item._load_item_config()
        item_data = item_config.get(item_id, {})

        price = item_data.get("price", 0)
        try:
            return int(price)
        except (TypeError, ValueError):
            return 0

    def __init__(self, game, item_id):
        super().__init__(game, self.sprite_from_item_id(item_id), text_label=item_id)
        self.item_id = item_id
        self.price = self.price_from_item_id(self.item_id)
        self.time_off_belt = 0

    def _get_belt_under_item(self):
        from objects.belt import Belt

        size = self.game.SIZE_PER_TILE
        item_center = (self.position[0] + (size / 2), self.position[1] + (size / 2))

        for obj in self.game.objects:
            if not isinstance(obj, Belt):
                continue

            belt_x, belt_y = obj.position
            if (
                belt_x <= item_center[0] < belt_x + size
                and belt_y <= item_center[1] < belt_y + size
            ):
                return obj

        return None

    def move(self, position):
        self.position = position

    def update(self, dt, events):
        super().update(dt, events)

        belt = self._get_belt_under_item()
        if belt is not None:
            belt.check_move(self, dt)
            self.time_off_belt = 0
            return

        self.time_off_belt += dt / 1000
        if self.time_off_belt > 5:
            self.remove_from_game()

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "item"
        data["item_id"] = self.item_id
        data["time_off_belt"] = self.time_off_belt
        return data

    @staticmethod
    def from_dict(game, data):
        instance = Item(
            game,
            item_id=data.get("item_id", "unknown"),
        )
        instance.set_position(data.get("position", (0, 0)))
        instance.direction = data.get("direction", 1)
        instance.time_off_belt = data.get("time_off_belt", 0)
        return instance
