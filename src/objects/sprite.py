from __future__ import annotations


from src.static_config import CULLING_DISABLED, GRID_SIZE, SPRITE_LAYER
from pygame import SRCALPHA, Surface, Vector2, draw, freetype, transform
from src.classes.game_object import GameObject
from src.classes.image_cache import ImageCache
from pygame.sprite import DirtySprite
from typing import TYPE_CHECKING
from pygame.rect import Rect


if TYPE_CHECKING:
    from pygame.typing import FileLike

    from src.game import Game


class GameObjectDirtySprite(DirtySprite):
    def __init__(
        self,
        game: Game,
        position: Vector2 | None = None,
        size: Vector2 | None = None,
        rotation: int = 0,
        *groups,  # type: ignore
    ):

        super().__init__(groups)  # type: ignore
        self.game = game
        self._position = position if position else Vector2(0, 0)
        self._size = size if size else Vector2(1, 1)
        self._rotation = rotation % 360
        self._active = True
        self.destroyed = False

        self.game.camera.on("resize", self.__update_visibility)
        self.game.camera.on("move", self.__update_visibility)
        self.game.camera.on("zoom", self.__update_visibility)
        self.__update_visibility()

    def __del__(self):
        self.destroy()

    ####

    def __update_visibility(self):
        world_rect = Rect(
            self._position.x,
            self._position.y,
            self.size.x * GRID_SIZE,
            self.size.y * GRID_SIZE,
        )
        self._visible = CULLING_DISABLED or (
            not self.destroyed
            and self._active
            and self.game.camera.is_in_camera(world_rect)
        )
        self.dirty = 1

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        self.dirty = 1
        self.__update_visibility()

    @property
    def rect(self) -> Rect:  # type: ignore
        pos = self.game.camera.world_to_screen(self.position)
        zoom = self.game.camera.zoom
        return Rect(
            pos.x,
            pos.y,
            self._size.x * GRID_SIZE * zoom,
            self._size.y * GRID_SIZE * zoom,
        )

    @property
    def visible(self) -> int:  # type: ignore
        return 1 if not self.destroyed and self._active and self._visible else 0

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value: Vector2):
        self._position = value
        self.__update_visibility()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value: Vector2):
        self._size = value
        self.__update_visibility()

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value: int):
        self._rotation = value
        self.__update_visibility()

    def should_cull(self):
        return not CULLING_DISABLED and (
            not self._active
            or not self.game.camera.is_in_camera(
                (
                    self._position.x,
                    self._position.y,
                    self._size.x * GRID_SIZE,
                    self._size.y * GRID_SIZE,
                )
            )
        )

    def destroy(self):
        self.game.camera.remove_listener("resize", self.__update_visibility)
        self.game.camera.remove_listener("move", self.__update_visibility)
        self.game.camera.remove_listener("zoom", self.__update_visibility)


class Sprite(GameObject):
    def __init__(
        self,
        game: Game,
        file: FileLike,
        position: Vector2 | None = None,
        size: Vector2 | None = None,
        rotation: int = 0,
        layer: SPRITE_LAYER = SPRITE_LAYER.DEFAULT,
    ):
        self.game = game
        self.sprite = GameObjectDirtySprite(
            self.game,
            position=position,
            size=size,
            rotation=rotation,
        )

        self._position = position
        self._rotation = rotation

        self._base_image = self._load_image_or_placeholder(file)
        self._refresh_image()

        self.game.camera.on("zoom", self._on_zoom)

        self.game.sprite_layers.add(self.sprite, layer=layer)
        super().__init__(game, position, size, rotation, track_camera_visibility=False)

    def _build_placeholder_image(self, file: FileLike) -> Surface:
        width = int(max(1, self.sprite.size.x) * GRID_SIZE)
        height = int(max(1, self.sprite.size.y) * GRID_SIZE)
        placeholder = Surface((width, height), SRCALPHA).convert_alpha()

        placeholder.fill((255, 80, 80, 255))
        draw.rect(placeholder, (35, 35, 35, 255), placeholder.get_rect(), width=3)

        if not freetype.get_init():
            freetype.init()

        text_font = freetype.SysFont("Arial", 11, bold=True)
        path_text = str(file)
        max_width = max(8, width - 10)

        lines: list[str] = []
        current = ""
        for chunk in path_text.split("/"):
            chunk = chunk if current == "" else f"/{chunk}"
            trial = f"{current}{chunk}"
            if current and text_font.get_rect(trial).width > max_width:
                lines.append(current)
                current = chunk
            else:
                current = trial
        if current:
            lines.append(current)

        y = 6
        for line in lines[: max(1, (height - 8) // 12)]:
            text_surface, _ = text_font.render(line, (20, 20, 20, 255))
            placeholder.blit(text_surface, (5, y))
            y += 12

        return placeholder

    def _load_image_or_placeholder(self, file: FileLike) -> Surface:
        loaded = ImageCache.get(file)
        if loaded is not None:
            return loaded
        return self._build_placeholder_image(file)

    def _refresh_image(self):
        image = self._base_image

        if self.sprite.rotation != 0:
            image = transform.rotate(image, self.sprite.rotation)

        if abs(self.game.camera.zoom - 1.0) > 1e-6:
            width = max(1, int(round(image.get_width() * self.game.camera.zoom)))
            height = max(1, int(round(image.get_height() * self.game.camera.zoom)))
            image = transform.scale(image, (width, height))

        self.sprite.image = image
        self.sprite.dirty = 1

    def _on_zoom(self):
        self._refresh_image()

    @property
    def active(self):
        return self.sprite.active

    @active.setter
    def active(self, value: bool):
        self.sprite.active = value

    @property
    def destroyed(self):
        return self.sprite.destroyed

    @destroyed.setter
    def destroyed(self, value: bool):
        self.sprite.destroyed = value

    @property
    def visible(self):
        return self.sprite.visible == 1

    @visible.setter
    def visible(self, value: bool):  # type: ignore
        pass

    @property
    def position(self):
        return self.sprite.position

    @position.setter
    def position(self, value: Vector2):
        self._update_position_map(value, self.sprite.position)
        self.sprite.position = value
        self._position = value

    @property
    def rotation(self) -> int:
        return self.sprite.rotation

    @rotation.setter
    def rotation(self, value: int):
        value = value % 360
        self.sprite.rotation = value
        self._refresh_image()
        self._rotation = value

    @property
    def size(self) -> Vector2:
        return self.sprite.size

    @size.setter
    def size(self, value: Vector2):
        self.sprite.size = value

    def destroy(self):
        self.game.camera.remove_listener("zoom", self._on_zoom)
        self.game.sprite_layers.remove(self.sprite)
        self.sprite.destroy()
        super().destroy()
