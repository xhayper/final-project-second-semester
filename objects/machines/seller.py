from objects.machine import Machine
from objects.item import Item


class Seller(Machine):
    def __init__(self, game, pos=(0, 0)):
        super().__init__(game, "seller", pos)

    def insert_item(self, obj: Item):
        item_price = Item.price_from_item_id(obj.item_id)
        self.game.statistics.increment("items_sold")
        self.game.add_cash(item_price)
        obj.remove_from_game()
        return True

    def to_dict(self):
        obj = super().to_dict()
        obj["type"] = "seller"
        del obj["inventory"]
        return obj

    @staticmethod
    def from_dict(game, data):
        instance = Seller(game, pos=data.get("position", (0, 0)))
        instance.direction = data.get("direction", 1)
        return instance
