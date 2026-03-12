from __future__ import annotations

from src.objects.machine import Machine
from typing import TYPE_CHECKING, Any
from pygame import Vector2

if TYPE_CHECKING:
    from src.game import Game


class Seller(Machine):
    def __init__(
        self,
        game: Game,
        position: Vector2 | None = None,
        rotation: int = 0,
    ):
        super().__init__(
            game,
            type="seller",
            position=position,
            size=Vector2(1, 1),
            rotation=rotation,
        )

    def __del__(self):
        self.destroy()

    ####

    def insert_item(self, type: str):
        item_data = self.game.data.get_item_data(type)
        self.game.data.cash += item_data["price"]
        self.game.data.statistics.record_item_sold(type, amount=1)
        self.game.data.statistics.record_cash_earned(
            int(item_data["price"]),
            source=f"seller:{type}",
        )

    def output_item(self, type: str):
        pass

    def update(self, dt: float):
        pass

    # Serialization

    def to_dict(self) -> dict[str, Any]:
        return {
            "class": "seller",
            "position": (int(self.position.x), int(self.position.y)),
            "rotation": int(self.rotation),
        }

    @classmethod
    def from_dict(cls, game: Game, data: dict[str, Any]):
        pos = data.get("position", (0, 0))
        return cls(
            game,
            position=Vector2(pos[0], pos[1]),
            rotation=int(data.get("rotation", 0)),
        )
