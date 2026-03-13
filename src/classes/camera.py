from __future__ import annotations

from pygame import Rect, Vector2, display
from typing import TYPE_CHECKING, Any
from . import EventEmitter
import pygame


if TYPE_CHECKING:
    from pygame.typing import RectLike
    from src.game import Game


class Camera(EventEmitter):
    def __init__(self, game: Game, position: Vector2 | None = None):
        super().__init__()

        self.game = game
        self._position = position if position else Vector2(0)
        self._size = Vector2(display.get_window_size())
        self._zoom = 1.0
        self._min_zoom = 0.5
        self._max_zoom = 3.0

        self.game.on(f"PYGAME_{pygame.WINDOWRESIZED}", self.__on_window_resized)

    def __on_window_resized(self, value: dict[str, Any]):
        self._size = Vector2(value["x"], value["y"])
        self.game.request_flip()
        self.emit("resize")

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def min_zoom(self) -> float:
        return self._min_zoom

    @property
    def max_zoom(self) -> float:
        return self._max_zoom

    @property
    def position(self) -> Vector2:
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value
        self.emit("move")

    def set_zoom(self, value: float, focus_screen_pos: Vector2 | None = None):
        clamped = max(self._min_zoom, min(self._max_zoom, float(value)))
        if abs(clamped - self._zoom) < 1e-6:
            return

        focus = focus_screen_pos if focus_screen_pos is not None else self._size / 2
        world_before = self.screen_to_world(focus)
        self._zoom = clamped
        self._position = world_before - (focus / self._zoom)

        self.game.request_flip()
        self.emit("move")
        self.emit("zoom")

    def adjust_zoom(self, delta: float, focus_screen_pos: Vector2 | None = None):
        self.set_zoom(self._zoom + delta, focus_screen_pos)

    @property
    def rect(self) -> Rect:
        return Rect(
            self.position.x,
            self.position.y,
            self._size.x / self._zoom,
            self._size.y / self._zoom,
        )

    def world_to_screen(self, pos: Vector2) -> Vector2:
        delta = pos - self.position
        return Vector2(delta.x * self._zoom, delta.y * self._zoom)

    def screen_to_world(self, pos: Vector2) -> Vector2:
        return Vector2(
            (pos.x / self._zoom) + self.position.x,
            (pos.y / self._zoom) + self.position.y,
        )

    def is_in_camera(self, rect: RectLike):
        return self.rect.colliderect(rect)

    def destroy(self):
        self.game.remove_listener(
            f"PYGAME_{pygame.WINDOWRESIZED}", self.__on_window_resized
        )
        self.remove_all_listeners()
