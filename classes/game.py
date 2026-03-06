from objects.engines.camera import Camera
from objects.engines.input import Input
from objects.belt import Belt
from objects.item import Item
from objects.machine import Machine
from objects.machines.miner import Miner
from objects.machines.seller import Seller
from typing import TYPE_CHECKING, List, Dict, Tuple

from objects.engines.ui import UI
from .statistics import Statistics
import pygame
import time
import math
import json
from pathlib import Path

if TYPE_CHECKING:
    from objects.game_object import GameObject


class Game:
    SIZE_PER_TILE = 64
    DEBUG = False

    FONTS: Dict[str, pygame.Font] = {}

    def __init__(self):
        pygame.init()

        self.FONTS["Arial"] = pygame.font.SysFont("Arial", 18)
        self.FONTS["Comic Sans MS"] = pygame.font.SysFont("Comic Sans MS", 18)

        pygame.display.set_caption("Funky Factory Game")
        pygame.display.set_icon(self.FONTS["Arial"].render("FFG", True, "White"))

        self.screen = pygame.display.set_mode((1280, 720))
        self.statistics = Statistics()
        self.ui = UI(self)
        self.input_object = Input(self)
        self.camera = Camera(self)
        self.cash = 0

        self.objects: List[GameObject] = [self.camera, self.ui, self.input_object]
        self.start_time = math.floor(time.time())

        self.position_map: Dict[Tuple[int, int], List[GameObject]] = {}

        if not self.load_game("save.json"):
            pass

    def save_game(self, filename: str):
        save_data = {
            "cash": self.cash,
            "objects": [],
        }

        for obj in self.objects:
            if obj in [self.input_object, self.camera, self.ui]:
                continue

            obj_data = obj.to_dict()
            if obj_data is not None:
                save_data["objects"].append(obj_data)

        path = Path.cwd() / filename
        with open(path, "w") as f:
            json.dump(save_data, f)

    def load_game(self, filename: str) -> bool:
        path = Path.cwd() / filename
        save_data = {}

        if path.exists():
            try:
                with open(path, "r") as f:
                    save_data = json.load(f)
            except Exception as e:
                print(f"Failed to load save from {filename}: {e}")
                return False

        self.cash = save_data.get("cash", 11)
        self.objects = [self.input_object, self.camera, self.ui]
        for obj_data in save_data.get("objects", []):
            obj_type = obj_data.get("type")
            obj = None
            if obj_type == "belt":
                obj = Belt.from_dict(self, obj_data)
            elif obj_type == "item":
                obj = Item.from_dict(self, obj_data)
            elif obj_type == "machine":
                obj = Machine.from_dict(self, obj_data)
            elif obj_type == "seller":
                obj = Seller.from_dict(self, obj_data)
            elif obj_type == "miner":
                obj = Miner.from_dict(self, obj_data)
            if obj:
                obj.add_to_game()
                if obj_type != "item":
                    obj.snap_to_grid()
        return True

    def add_object(self, obj: GameObject):
        self.objects.append(obj)
        if obj.grid_position not in self.position_map:
            self.position_map[obj.grid_position] = [obj]
        else:
            self.position_map[obj.grid_position].append(obj)

    def remove_object(self, obj: GameObject):
        if obj in self.objects:
            self.objects.remove(obj)

        if obj.grid_position not in self.position_map:
            return

        if obj in self.position_map[obj.grid_position]:
            self.position_map[obj.grid_position].remove(obj)
        if len(self.position_map[obj.grid_position]) <= 0:
            del self.position_map[obj.grid_position]

    def add_cash(self, amount):
        if amount <= 0:
            return
        self.cash += amount
        self.statistics.increment("cash_earned", amount)

    def remove_cash(self, amount):
        if amount <= 0:
            return 0
        removed = min(self.cash, amount)
        self.cash -= removed
        return removed

    def draw_debug(self, screen: pygame.Surface):
        if not self.DEBUG:
            return

        grid_pos = (
            self.camera.to_world_position(pygame.mouse.get_pos())[0]
            // self.SIZE_PER_TILE,
            self.camera.to_world_position(pygame.mouse.get_pos())[1]
            // self.SIZE_PER_TILE,
        )

        elements = [
            self.FONTS["Arial"].render(f"Cash: {self.cash}", True, "White"),
            self.FONTS["Arial"].render(
                f"Mouse Pos: {pygame.mouse.get_pos()}", True, "White"
            ),
            self.FONTS["Arial"].render(
                f"Pos: {self.camera.to_world_position(pygame.mouse.get_pos())}",
                True,
                "White",
            ),
            self.FONTS["Arial"].render(
                f"Grid Pos: {grid_pos}",
                True,
                "White",
            ),
            self.FONTS["Arial"].render(
                f"Obj count: {len(self.objects)}", True, "White"
            ),
            self.FONTS["Arial"].render(
                f"Selected: {self.input_object.selected_obj}", True, "White"
            ),
            self.FONTS["Arial"].render(
                f"Mode: {self.input_object.mode}", True, "White"
            ),
        ]

        for x in range(len(elements)):
            screen.blit(
                elements[x],
                (0, (x * 18) + 32),
            )

    def start(self):
        try:
            is_running = True
            clock = pygame.Clock()
            dt = 0

            while is_running:
                self.screen.fill("black")

                events = pygame.event.get()

                for x in events:
                    if x.type == pygame.QUIT:
                        is_running = False
                        break

                if not is_running:
                    break

                for object in self.objects:
                    object.update(dt, events)

                self.draw_debug(self.screen)

                for object in self.objects:
                    if object.force_render or self.camera.is_in_camera_view(
                        object.position
                    ):
                        object.render(self.screen)

                pygame.display.flip()
                dt = clock.tick(60)
        except KeyboardInterrupt:
            pass

        pygame.quit()
        self.save_game("save.json")
        self.statistics.increment("playtime", math.floor(time.time()) - self.start_time)
        self.statistics.save_data("statistics.json")
