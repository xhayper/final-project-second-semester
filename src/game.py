from __future__ import annotations

from src.scenes import GameScene, LoadingScene, MainMenuScene, SceneManager
from src.classes.event_emitter import LISTENER_LIST, EventEmitter
from pygame import Clock, Rect, Surface, display, event
from pygame.sprite import DirtySprite, LayeredDirty
from typing import TYPE_CHECKING, Any, Callable
from src.classes.camera import Camera
from src.classes.input import Input
from src.classes.data import Data
from src.classes.ui import UI
import logging
import pygame

if TYPE_CHECKING:
    from src.classes.game_object import GameObject
    from pygame import FRect


# Got this formatter from the internet
def setup_logger(level: int):
    logger = logging.getLogger("Funky Factory Game")
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "RESET": "\033[0m",
    }

    class ColoredFormatter(logging.Formatter):
        def format(self, record: Any):
            color = COLORS.get(record.levelname, COLORS["RESET"])
            record.levelname = f"{color}[{record.levelname}]{COLORS['RESET']}"
            record.name = f"\033[1m{record.name}\033[0m"
            return f"{record.name} {record.levelname} → {record.getMessage()}"

    formatter = ColoredFormatter()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


class Game(EventEmitter):
    DEBUG = True

    def __init__(self):
        super().__init__()

        self.logger = setup_logger(logging.DEBUG if self.DEBUG else logging.INFO)
        self.logger.debug("Start")

        self.surface = display.set_mode((1280, 720), pygame.RESIZABLE)
        self.surface.fill((0, 0, 0))

        self.sprite_layers: LayeredDirty[DirtySprite] = LayeredDirty(default_layer=1)
        self.scene_manager = SceneManager(self)
        self.scene_manager.add_scene(LoadingScene(self))
        self.scene_manager.add_scene(MainMenuScene(self))
        self.scene_manager.add_scene(GameScene(self))
        self.scene_manager.change_scene("loading")
        self.active_save_path = "saves/save_1.data"

        self.data = Data(self)
        self._camera: Camera | None = None
        self._input: Input | None = None
        self._ui: UI | None = None
        self.bg = Surface((1280, 720))
        self.bg.fill("black")

        display.set_caption("Funky Factory Game")

        self.__requested_flip = True

    @property
    def camera(self) -> Camera:
        if self._camera is None:
            raise RuntimeError("Camera is not initialized yet")
        return self._camera

    @property
    def input(self) -> Input:
        if self._input is None:
            raise RuntimeError("Input is not initialized yet")
        return self._input

    @property
    def ui(self) -> UI:
        if self._ui is None:
            raise RuntimeError("UI is not initialized yet")
        return self._ui

    @property
    def runtime_systems_ready(self) -> bool:
        return (
            self._camera is not None
            and self._input is not None
            and self._ui is not None
        )

    def initialize_runtime_systems(self):
        if (
            self._camera is not None
            and self._input is not None
            and self._ui is not None
        ):
            return

        self._camera = Camera(self)
        self._input = Input(self)
        self._ui = UI(self)
        self.request_flip(rebuild_bg=True)

    @property
    def objects(self) -> list[GameObject]:
        if self.scene_manager.current_scene is None:
            return []
        return self.scene_manager.current_scene.objects

    @objects.setter
    def objects(self, value: list[GameObject]):
        if self.scene_manager.current_scene is None:
            return
        self.scene_manager.current_scene.objects = value

    @property
    def position_map(self) -> dict[tuple[int, int], list[GameObject]]:
        if self.scene_manager.current_scene is None:
            return {}
        return self.scene_manager.current_scene.position_map

    @position_map.setter
    def position_map(self, value: dict[tuple[int, int], list[GameObject]]):
        if self.scene_manager.current_scene is None:
            return
        self.scene_manager.current_scene.position_map = value

    def request_flip(self, rebuild_bg: bool = True):
        if rebuild_bg:
            self.bg = Surface(display.get_window_size())
            self.bg.fill("black")
        self.__requested_flip = True

    def render_game_scene(
        self, surface: Surface, overlay_draw: Callable[[Surface], None] | None = None
    ):
        if self._camera is None:
            return

        if self.__requested_flip:
            self.surface.fill("black")
        else:
            self.sprite_layers.clear(self.surface, self.bg)

        rects: list[FRect | Rect] = []
        for x in self.sprite_layers.draw(self.surface):
            if x.width > 0 or x.height > 0:
                rects.append(x)

        if self.DEBUG and False:
            if self.__requested_flip:
                self.logger.debug("FULL REDRAW!")
            elif len(rects) > 0:
                self.logger.debug("Got draw request for => %s", rects)
            else:
                self.logger.debug("No draw request")

        if overlay_draw is not None:
            overlay_draw(surface)

        if self.__requested_flip:
            display.flip()
            self.__requested_flip = False
        else:
            display.update(rects)

    def start(self):
        try:
            running = True
            clock = Clock()
            dt = 0

            while running:
                events = event.get()

                for evt in events:
                    if evt.type == pygame.QUIT:
                        running = False
                        break
                    self.scene_manager.handle_event(evt)

                if not running:
                    break

                self.scene_manager.update(dt)
                self.scene_manager.render(self.surface)

                if self.scene_manager.current_name != "game":
                    display.flip()

                dt = clock.tick(60) / 1000
        except KeyboardInterrupt:
            pass

        self.emit("quit")

        self.logger.debug("Shutting down!")

        pygame.quit()

        for emitter in LISTENER_LIST:
            emitter.remove_all_listeners()

        if "game" in ["loading", "main_menu", "game"]:
            game_scene = self.scene_manager.get_scene("game")
            if len(game_scene.objects) > 0:
                previous = self.scene_manager.current_scene
                self.scene_manager.current_scene = game_scene
                self.data.save(self.active_save_path)
                self.scene_manager.current_scene = previous

        if self._camera is not None:
            self._camera.destroy()
        if self._input is not None:
            self._input.destroy()
        if self._ui is not None:
            self._ui.destroy()
        self.scene_manager.destroy()
