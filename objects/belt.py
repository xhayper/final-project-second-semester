from objects.sprite import Sprite
from objects.item import Item
from objects.machine import Machine


class Belt(Sprite):
    SPEED = 1

    def __init__(self, game, pos=(0, 0)):
        super().__init__(game, "assets/belt.png", pos)
        self.direction = 1
        self.cost = 1

    def update(self, dt, events):
        super().update(dt, events)

    def check_move(self, obj: Item, dt: int):
        dx, dy = self._direction_vector()
        movement = self.SPEED * self.game.SIZE_PER_TILE * (dt / 1000)
        obj.set_position(
            (obj.position[0] + (dx * movement), obj.position[1] + (dy * movement))
        )

        size = self.game.SIZE_PER_TILE
        item_center = (obj.position[0] + (size / 2), obj.position[1] + (size / 2))

        for game_object in self.game.objects:
            if not isinstance(game_object, Machine):
                continue

            machine_x, machine_y = game_object.position
            if (
                machine_x <= item_center[0] < machine_x + size
                and machine_y <= item_center[1] < machine_y + size
            ):
                game_object.insert_item(obj)
                break

        return True

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "belt"
        return data

    @staticmethod
    def from_dict(game, data):
        instance = Belt(game, pos=data.get("position", (0, 0)))
        instance.direction = data.get("direction", 1)
        return instance
