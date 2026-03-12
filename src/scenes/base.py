from __future__ import annotations

from src.classes import EventEmitter
from typing import TYPE_CHECKING
from pygame import Surface
import pygame

if TYPE_CHECKING:
    from src.classes.game_object import GameObject
    from src.game import Game


class Scene(EventEmitter):
    def __init__(self, game: Game, name: str):
        super().__init__()
        self.game = game
        self.name = name
        self.objects: list[GameObject] = []
        self.position_map: dict[tuple[int, int], list[GameObject]] = {}

    def enter(self):
        pass

    def exit(self):
        pass

    def handle_event(self, evt: pygame.event.Event):
        pass

    def update(self, dt: float):
        pass

    def render(self, surface: Surface):
        pass
