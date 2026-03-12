from __future__ import annotations

from src.statistics import launch_statistics_window
from pygame import Rect, Surface, draw, freetype
from src.scenes.base import Scene
from typing import TYPE_CHECKING
from pygame.event import Event
from pygame import time
import pygame
import os

if TYPE_CHECKING:
    from src.game import Game


class MainMenuScene(Scene):
    def __init__(self, game: Game):
        super().__init__(game, "main_menu")

        if not freetype.get_init():
            freetype.init()
        self._title_font = freetype.SysFont("Arial", 40, bold=True)
        self._label_font = freetype.SysFont("Arial", 22, bold=True)
        self._hint_font = freetype.SysFont("Arial", 18, bold=False)

        self._show_slots = False
        self._play_rect = Rect(0, 0, 0, 0)
        self._stats_rect = Rect(0, 0, 0, 0)
        self._exit_rect = Rect(0, 0, 0, 0)
        self._slot_rects: list[Rect] = []
        self._back_rect = Rect(0, 0, 0, 0)
        self._slot_mode: str | None = None
        self._status_text: str | None = None
        self._status_text_expires_at = 0

    def _set_status_text(self, text: str, duration_ms: int = 900):
        self._status_text = text
        self._status_text_expires_at = time.get_ticks() + duration_ms

    def _slot_path(self, slot: int) -> str:
        return f"saves/save_{slot}.data"

    def _is_click_inside(self, evt: Event, rect: Rect) -> bool:
        if evt.type != pygame.MOUSEBUTTONDOWN:
            return False
        if getattr(evt, "button", 0) != 1:
            return False
        return rect.collidepoint(evt.pos)

    def _draw_button(self, surface: Surface, rect: Rect, label: str):
        draw.rect(surface, (36, 39, 45), rect, border_radius=8)
        draw.rect(surface, (140, 160, 180), rect, width=2, border_radius=8)
        text, _ = self._label_font.render(label, (235, 235, 235))
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)

    def enter(self):
        self._show_slots = False
        self.game.request_flip(rebuild_bg=True)
        self._slot_mode = None
        self._status_text = None
        self._status_text_expires_at = 0

    def handle_event(self, evt: Event):
        if evt.type == pygame.KEYDOWN and evt.key == pygame.K_ESCAPE:
            pygame.event.post(Event(pygame.QUIT))
            return

        if self._show_slots:
            if self._is_click_inside(evt, self._back_rect):
                self._show_slots = False
                self._slot_mode = None
                return

            for idx, rect in enumerate(self._slot_rects, start=1):
                if self._is_click_inside(evt, rect):
                    slot_path = self._slot_path(idx)

                    if self._slot_mode == "stats":
                        self._set_status_text("Starting statistics viewer...")
                        launched = launch_statistics_window(slot_path)
                        if not launched:
                            self._set_status_text(
                                "Failed to start statistics viewer",
                                duration_ms=1800,
                            )
                    else:
                        self.game.active_save_path = slot_path
                        self.game.scene_manager.change_scene("game")
                    return

            return

        if self._is_click_inside(evt, self._play_rect):
            self._show_slots = True
            self._slot_mode = "play"
            return

        if self._is_click_inside(evt, self._stats_rect):
            self._show_slots = True
            self._slot_mode = "stats"
            return

        if self._is_click_inside(evt, self._exit_rect):
            pygame.event.post(Event(pygame.QUIT))

    def render(self, surface: Surface):
        surface.fill((12, 12, 15))

        title, _ = self._title_font.render("Funky Factory Game", (245, 245, 245))
        center = surface.get_rect().center
        title_rect = title.get_rect(center=(center[0], center[1] - 170))

        surface.blit(title, title_rect)

        panel = Rect(0, 0, 440, 330 if self._show_slots else 270)
        panel.center = center
        draw.rect(surface, (20, 22, 28), panel, border_radius=12)
        draw.rect(surface, (95, 110, 130), panel, width=2, border_radius=12)

        self._play_rect = Rect(panel.x + 60, panel.y + 70, panel.width - 120, 50)
        self._stats_rect = Rect(panel.x + 60, panel.y + 135, panel.width - 120, 50)
        self._exit_rect = Rect(panel.x + 60, panel.y + 200, panel.width - 120, 50)

        if not self._show_slots:
            self._draw_button(surface, self._play_rect, "Play")
            self._draw_button(surface, self._stats_rect, "Statistics")
            self._draw_button(surface, self._exit_rect, "Exit")
            return

        title_text = (
            "Choose Statistics Slot"
            if self._slot_mode == "stats"
            else "Choose Save Slot"
        )
        slots_title, _ = self._hint_font.render(title_text, (170, 170, 170))
        slots_title_rect = slots_title.get_rect(center=(panel.centerx, panel.y + 36))
        surface.blit(slots_title, slots_title_rect)

        self._slot_rects = []
        start_y = panel.y + 70
        for idx in range(1, 4):
            slot_rect = Rect(
                panel.x + 40, start_y + ((idx - 1) * 60), panel.width - 80, 50
            )
            self._slot_rects.append(slot_rect)

            state = "USED" if os.path.exists(self._slot_path(idx)) else "EMPTY"
            self._draw_button(surface, slot_rect, f"Slot {idx}  [{state}]")

        self._back_rect = Rect(panel.x + 140, panel.bottom - 60, panel.width - 280, 40)
        self._draw_button(surface, self._back_rect, "Back")

        if (
            self._status_text is not None
            and time.get_ticks() <= self._status_text_expires_at
        ):
            status, _ = self._hint_font.render(self._status_text, (155, 205, 155))
            status_rect = status.get_rect(center=(panel.centerx, panel.bottom + 24))
            surface.blit(status, status_rect)
