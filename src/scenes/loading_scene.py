from __future__ import annotations

from src.classes.image_cache import ImageCache
from typing import TYPE_CHECKING, Callable
from pygame import Surface, freetype
from src.classes.data import Data
from src.scenes.base import Scene

if TYPE_CHECKING:
    from src.game import Game


class LoadingScene(Scene):
    def __init__(self, game: Game):
        super().__init__(game, "loading")
        self._tasks: list[tuple[str, Callable[[], None]]] = []
        self._total_tasks = 0
        self._completed_tasks = 0
        self._status_text = "Preparing loader..."
        self._preloaded_count = 0
        self._failed_count = 0
        self._failed_list: list[str] = []
        self._loaded_list: list[str] = []
        self._built_sprite_tasks = False
        self._loading_done = False

        if not freetype.get_init():
            freetype.init()
        self._font = freetype.SysFont("Arial", 30, bold=True)
        self._status_font = freetype.SysFont("Arial", 18, bold=False)

    def _load_items(self):
        Data.LOAD_ITEMS()

    def _load_machines(self):
        Data.LOAD_MACHINES()

    def _build_sprite_preload_tasks(self):
        if self._built_sprite_tasks:
            return

        sprite_paths = Data.get_sprite_paths()
        sprite_tasks: list[tuple[str, Callable[[], None]]] = []

        for path in sprite_paths:

            def load_sprite(sprite_path: str = path):
                loaded = ImageCache.get(sprite_path)
                if loaded is None:
                    self._failed_list.append(sprite_path)
                    self._failed_count += 1
                else:
                    self._loaded_list.append(sprite_path)
                    self._preloaded_count += 1

            sprite_tasks.append((f"Preloading sprite: {path}", load_sprite))

        self._tasks.extend(sprite_tasks)
        self._tasks.append(
            ("Preparing runtime systems...", self.game.initialize_runtime_systems)
        )
        self._total_tasks += len(sprite_tasks) + 1
        self._built_sprite_tasks = True

    def _next_task(self) -> tuple[str, Callable[[], None]] | None:
        if not self._tasks:
            return None
        return self._tasks.pop(0)

    @property
    def _progress_ratio(self) -> float:
        if self._total_tasks <= 0:
            return 0.0
        return min(1.0, self._completed_tasks / self._total_tasks)

    def enter(self):
        self._tasks = [
            ("Loading item data...", self._load_items),
            ("Loading machine data...", self._load_machines),
        ]
        self._total_tasks = len(self._tasks)
        self._completed_tasks = 0
        self._status_text = "Starting loading..."
        self._preloaded_count = 0
        self._failed_count = 0
        self._built_sprite_tasks = False
        self._loading_done = False
        self.game.request_flip(rebuild_bg=True)

    def update(self, dt: float):
        del dt

        self.game.logger.debug(self._status_text)

        if self._loading_done:
            self.game.scene_manager.change_scene("main_menu")
            return

        task = self._next_task()
        if task is None:
            self._status_text = "Ready"
            self._loading_done = True
            self.game.logger.debug(
                "Preloaded sprites: loaded=%d failed=%d",
                self._preloaded_count,
                self._failed_count,
            )

            for path in self._failed_list:
                self.game.logger.error("Failed to load sprite: %s", path)
            for path in self._loaded_list:
                self.game.logger.debug("Successfully loaded sprite: %s", path)
            return

        status, task_fn = task
        self._status_text = status
        task_fn()
        self._completed_tasks += 1

        if status == "Loading machine data...":
            self._build_sprite_preload_tasks()

    def render(self, surface: Surface):
        surface.fill((8, 8, 10))
        text, _ = self._font.render("Loading...", (220, 220, 220))
        rect = text.get_rect(
            center=(surface.get_rect().centerx, surface.get_rect().centery - 40)
        )
        surface.blit(text, rect)

        progress_percent = int(self._progress_ratio * 100)
        status_line = f"{self._status_text} ({progress_percent}%)"
        status_text, _ = self._status_font.render(status_line, (170, 170, 170))
        status_rect = status_text.get_rect(
            center=(surface.get_rect().centerx, surface.get_rect().centery + 5)
        )
        surface.blit(status_text, status_rect)

        bar_width = 360
        bar_height = 18
        bar_left = surface.get_rect().centerx - (bar_width // 2)
        bar_top = surface.get_rect().centery + 40
        fill_width = int(bar_width * self._progress_ratio)

        from pygame import draw, Rect

        draw.rect(
            surface,
            (45, 45, 45),
            Rect(bar_left, bar_top, bar_width, bar_height),
            border_radius=5,
        )
        draw.rect(
            surface,
            (80, 180, 110),
            Rect(bar_left, bar_top, fill_width, bar_height),
            border_radius=5,
        )
        draw.rect(
            surface,
            (120, 120, 120),
            Rect(bar_left, bar_top, bar_width, bar_height),
            width=2,
            border_radius=5,
        )

        summary_text, _ = self._status_font.render(
            f"Tasks: {self._completed_tasks}/{self._total_tasks}",
            (140, 140, 140),
        )
        summary_rect = summary_text.get_rect(
            center=(surface.get_rect().centerx, bar_top + bar_height + 20)
        )
        surface.blit(summary_text, summary_rect)
