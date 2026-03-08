from pygame import Vector2, Event, Rect, display
from typing import TYPE_CHECKING, List
import pygame

if TYPE_CHECKING:
    from pygame.typing import RectLike
    from src.game import Game


class Camera:
    def __init__(self, game: Game, position: Vector2 | None = None):
        self.game = game
        self._position = position if position else Vector2()
        self._size = Vector2(display.get_window_size())

    def __mark_sprite_as_dirty(self):
        for x in self.game.sprite_layers.sprites():
            x.dirty = 1

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value
        self.__mark_sprite_as_dirty()

    @property
    def rect(self):
        return Rect(
            self.position.x,
            self.position.y,
            self._size.x,
            self._size.y,
        )

    def world_to_screen(self, pos: Vector2):
        return pos - self.position

    def screen_to_world(self, pos: Vector2):
        return pos + self.position

    def is_in_camera(self, rect: RectLike):
        return self.rect.colliderect(rect)

    def update(self, dt: float, events: List[Event]):
        for event in events:
            if event.type == pygame.WINDOWRESIZED:
                self._size = Vector2(event.dict["x"], event.dict["y"])
                self.__mark_sprite_as_dirty()
                self.game.request_flip()
