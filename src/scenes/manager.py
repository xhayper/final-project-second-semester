from __future__ import annotations

from src.scenes.base import Scene
from typing import TYPE_CHECKING
from pygame import Surface
import pygame


if TYPE_CHECKING:
    from src.game import Game


class SceneManager:
    def __init__(self, game: Game):
        self.game = game
        self._scenes: dict[str, Scene] = {}
        self.current_scene: Scene | None = None

    @property
    def current_name(self) -> str:
        return self.current_scene.name if self.current_scene is not None else ""

    def add_scene(self, scene: Scene):
        self._scenes[scene.name] = scene

    def get_scene(self, name: str) -> Scene:
        return self._scenes[name]

    def change_scene(self, name: str):
        if self.current_scene is not None and self.current_scene.name == name:
            return

        if self.current_scene is not None:
            self.current_scene.exit()

        self.current_scene = self._scenes[name]
        self.current_scene.enter()

    def handle_event(self, evt: pygame.event.Event):
        if self.current_scene is None:
            return
        self.current_scene.handle_event(evt)

    def update(self, dt: float):
        if self.current_scene is None:
            return
        self.current_scene.update(dt)

    def render(self, surface: Surface):
        if self.current_scene is None:
            surface.fill((0, 0, 0))
            return
        self.current_scene.render(surface)

    def destroy(self):
        for scene in self._scenes.values():
            for obj in list(scene.objects):
                obj.destroy()
            scene.objects = []
            scene.position_map = {}
            scene.remove_all_listeners()
