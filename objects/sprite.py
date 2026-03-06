from typing import TYPE_CHECKING
from objects.game_object import GameObject
import pygame
from pathlib import Path

if TYPE_CHECKING:
    from classes.game import Game


class Sprite(GameObject):
    def __init__(self, game: "Game", file, pos=(0, 0), text_label=None):
        super().__init__(game, pos)
        self.text_label = text_label
        tile_size = game.SIZE_PER_TILE

        try:
            if isinstance(file, str) and Path(file).exists():
                self.image = pygame.image.load(file).convert_alpha()

                if self.image.get_size() != (tile_size, tile_size):
                    self.image = pygame.transform.scale(
                        self.image, (tile_size, tile_size)
                    )
            else:
                self.image = self._create_text_sprite(text_label or str(file))
        except (pygame.error, OSError):
            self.image = self._create_text_sprite(text_label or str(file))

    def _create_text_sprite(self, label):
        tile_size = self.game.SIZE_PER_TILE

        surface = pygame.Surface((tile_size, tile_size))
        surface.fill((50, 50, 50))

        font = self.game.FONTS["Arial"]
        text_surface = font.render(label[:10], True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(tile_size // 2, tile_size // 2))
        surface.blit(text_surface, text_rect)

        return surface

    def render(self, screen):
        super().render(screen)
        pos_x, pos_y = self.world_to_camera(
            (
                self.position[0] + (self.game.SIZE_PER_TILE / 2),
                self.position[1] + (self.game.SIZE_PER_TILE / 2),
            )
        )
        rotated = self.get_sprite()
        rect = rotated.get_rect()
        rect.center = (round(pos_x), round(pos_y))
        screen.blit(rotated, rect)

    def get_sprite(self):
        angle = (self.direction - 1) * -90
        rotated = pygame.transform.rotate(self.image, angle)

        return rotated

    def to_dict(self):
        data = super().to_dict()
        return data
