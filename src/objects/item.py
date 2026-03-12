from __future__ import annotations


from src.classes.data import Data, ItemData
from src.static_config import SPRITE_LAYER
from src.objects.sprite import Sprite
from typing import TYPE_CHECKING, Any
from src.objects.belt import Belt
from pygame import Vector2

if TYPE_CHECKING:
    from src.game import Game
    from src.objects.machine import Machine


class Item(Sprite):
    def __init__(
        self,
        game: Game,
        type: str | None = "unknown",
        data: ItemData | None = None,
        position: Vector2 | None = None,
        rotation: int = 0,
        track_statistics: bool = True,
    ):
        if data is None and type is None:
            raise ValueError("Invalid options! Choose either `type` or `data`")

        data = data if data is not None else Data.get_item_data(type)

        super().__init__(
            game,
            data["sprite"],
            position,
            Vector2(1, 1),
            rotation,
            layer=SPRITE_LAYER.ITEM,
        )

        self.price = data["price"]
        self.type = data["type"]
        self.machine: Machine | None = None
        self.belt: Belt | None = None
        self.despawn_timer = 0
        self._despawn_reason = "destroy"
        self._track_statistics = track_statistics

        if self._track_statistics:
            self.game.data.statistics.record_item_spawn(self.type, source="create")

        self.search_for_belt()
        self.game.on("update", self.update)

    def __del__(self):
        self.destroy()

    ####

    def search_for_belt(self):
        if self.belt is not None:
            return

        grid_pos = (int(self.grid_position.x), int(self.grid_position.y))

        if grid_pos not in self.game.position_map:
            return

        for x in self.game.position_map[grid_pos]:
            if isinstance(x, Belt):
                x.insert_item(self)
                self.despawn_timer = 0

    def search_for_machine(self):
        from src.objects.machine import Machine

        grid_pos = (int(self.grid_position.x), int(self.grid_position.y))

        if grid_pos not in self.game.position_map:
            return

        for x in self.game.position_map[grid_pos]:
            if isinstance(x, Machine) and not x.destroyed:
                x.insert_item(self.type)
                self.destroy()
                return

    @Sprite.position.setter
    def position(self, value: Vector2):  # type: ignore
        Sprite.position.fset(self, value)  # type: ignore
        self._position = value
        self.search_for_belt()

    def update(self, dt: float):
        if self.belt:
            return

        self.despawn_timer += dt

        if self.despawn_timer >= 15:
            self._despawn_reason = "timeout"
            if self._track_statistics:
                self.game.data.statistics.record_item_despawn(
                    self.type,
                    reason=self._despawn_reason,
                )
            self.destroy()

    def destroy(self):
        if self.destroyed:
            return

        self.game.remove_listener("update", self.update)
        super().destroy()

    def to_dict(self) -> dict[str, Any]:
        return {
            "class": "item",
            "item_type": self.type,
            "position": [int(self.position.x), int(self.position.y)],
            "rotation": int(self.rotation),
            "despawn_timer": self.despawn_timer,
        }

    @classmethod
    def from_dict(cls, game: Game, data: dict[str, Any]):
        pos = data.get("position", [0, 0])
        obj = cls(
            game,
            type=str(data.get("item_type", "unknown")),
            position=Vector2(pos[0], pos[1]),
            rotation=int(data.get("rotation", 0)),
            track_statistics=False,
        )
        obj.despawn_timer = float(data.get("despawn_timer", 0))
        return obj
