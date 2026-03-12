from __future__ import annotations

from typing import TYPE_CHECKING, Any
from src.objects import Machine, Item
from pygame import Vector2

if TYPE_CHECKING:
    from src.game import Game


class Miner(Machine):
    def __init__(
        self,
        game: Game,
        position: Vector2 | None = None,
        rotation: int = 0,
        ore_type: str = "copper",
        last_drop: float = 0,
    ):
        super().__init__(
            game,
            type="miner",
            position=position,
            size=Vector2(1, 1),
            rotation=rotation,
        )
        self.ore_type = ore_type
        self.timer = last_drop

    def __del__(self):
        self.destroy()

    ####

    def output_item(self, type: str):
        item = Item(self.game, position=self.get_forward(), type=type)
        self.game.objects.append(item)

    def update(self, dt: float):
        self.timer += dt

        if self.timer >= 3:
            self.output_item(f"{self.ore_type}_ore")
            self.timer = 0

    # Serialization

    def to_dict(self) -> dict[str, Any]:
        return {
            "class": "miner",
            "position": (int(self.position.x), int(self.position.y)),
            "rotation": int(self.rotation),
            "ore_type": self.ore_type,
            "timer": self.timer,
        }

    @classmethod
    def from_dict(cls, game: Game, data: dict[str, Any]):
        pos = data.get("position", (0, 0))
        return cls(
            game,
            position=Vector2(pos[0], pos[1]),
            rotation=int(data.get("rotation", 0)),
            ore_type=str(data.get("ore_type", "copper")),
            last_drop=float(data.get("timer", 0)),
        )
