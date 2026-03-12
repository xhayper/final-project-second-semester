from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, TypedDict, cast
from src.statistics import StatisticsTracker
import json
import os


if TYPE_CHECKING:
    from src.game import Game


class ItemQuantity(TypedDict):
    type: str
    amount: int


class MachineRecipeData(TypedDict):
    duration: float
    inputs: list[ItemQuantity]
    outputs: list[ItemQuantity]


class MachineData(TypedDict):
    type: str
    sprite: str
    cost: int
    recipes: list[MachineRecipeData]


class ItemData(TypedDict):
    type: str
    sprite: str
    price: int


class Data:
    MACHINE_DATA_PATH = "assets/data/machines.json"
    ITEMS_DATA_PATH = "assets/data/items.json"

    machine_data: dict[str, MachineData] = {
        "unknown": {
            "type": "unknown",
            "sprite": "assets/sprite/x.png",
            "cost": 99999999999999,
            "recipes": [],
        }
    }
    items_data: dict[str, ItemData] = {
        "unknown": {
            "type": "unknown",
            "sprite": "assets/sprite/x.png",
            "price": 99999999999999,
        }
    }

    @staticmethod
    def LOAD_ITEMS():
        with open(Data.ITEMS_DATA_PATH, "r", encoding="utf-8") as file:
            Data.items_data = json.load(file)

    @staticmethod
    def LOAD_MACHINES():
        with open(Data.MACHINE_DATA_PATH, "r", encoding="utf-8") as file:
            Data.machine_data = json.load(file)

    @staticmethod
    def get_machine_data(type: str | None = "unknown"):
        type = type if type is not None else "unknown"
        return (
            Data.machine_data[type]
            if type in Data.machine_data
            else Data.machine_data["unknown"]
        )

    @staticmethod
    def get_item_data(type: str | None = "unknown"):
        type = type if type is not None else "unknown"
        return (
            Data.items_data[type]
            if type in Data.items_data
            else Data.items_data["unknown"]
        )

    @staticmethod
    def get_sprite_paths() -> list[str]:
        paths: list[str] = [
            "assets/sprite/belt.png",
            "assets/unknown.png",
            "assets/sprite/x.png",
        ]

        for machine in Data.machine_data.values():
            paths.append(machine["sprite"])

        for item in Data.items_data.values():
            paths.append(item["sprite"])

        return list(dict.fromkeys(paths))

    #######

    def __init__(self, game: Game):
        self.game = game
        self.cash = 100
        self.statistics = StatisticsTracker()

    def _statistics_path(self, save_path: str) -> str:
        base, _ = os.path.splitext(save_path)
        return f"{base}.stats.json"

    def load(self, path: str = "save.data"):
        from src.objects.machine import Machine
        from src.machines.seller import Seller
        from src.machines.miner import Miner
        from src.objects.belt import Belt
        from src.objects.item import Item

        if not os.path.exists(path):
            payload_any: Any = {
                "cash": 100,
                "objects": [],
            }
        else:
            with open(path, "r", encoding="utf-8") as file:
                payload_any = json.load(file)

        if not isinstance(payload_any, dict):
            return

        payload = cast(dict[str, Any], payload_any)

        for obj in list(self.game.objects):
            obj.destroy()

        self.game.objects = []
        self.cash = int(payload.get("cash", 100))
        self.statistics.load_file(self._statistics_path(path))

        raw_objects: list[Any] = payload.get("objects", [])
        if not isinstance(raw_objects, list):  # type: ignore
            return

        objects: list[dict[str, Any]] = []
        for raw_obj in raw_objects:
            if isinstance(raw_obj, dict):
                objects.append(cast(dict[str, Any], raw_obj))

        constructor_map: dict[str, Callable[[Game, dict[str, Any]], Any]] = {
            "belt": Belt.from_dict,
            "machine": Machine.from_dict,
            "seller": Seller.from_dict,
            "miner": Miner.from_dict,
            "item": Item.from_dict,
        }

        order = {"belt": 0, "machine": 1, "seller": 1, "miner": 1, "item": 2}
        sorted_objects = sorted(
            objects, key=lambda x: order.get(str(x.get("class", "")), 99)
        )

        for obj_data in sorted_objects:
            kind = str(obj_data.get("class", ""))
            constructor = constructor_map.get(kind)
            if constructor is None:
                continue
            obj = constructor(self.game, obj_data)
            self.game.objects.append(obj)

    def save(self, path: str = "save.data"):
        objects: list[dict[str, Any]] = []
        for obj in self.game.objects:
            to_dict = getattr(obj, "to_dict", None)
            if callable(to_dict):
                serialized = to_dict()
                if isinstance(serialized, dict):
                    objects.append(cast(dict[str, Any], serialized))

        payload: dict[str, Any] = {
            "cash": int(self.cash),
            "objects": objects,
        }

        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

        self.statistics.save_file(self._statistics_path(path))
