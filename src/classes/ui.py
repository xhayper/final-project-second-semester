from __future__ import annotations


from src.static_config import GRID_SIZE, SPRITE_LAYER
from src.classes import EventEmitter, ImageCache
from pygame.sprite import DirtySprite
from src.objects import Machine, Belt
from typing import TYPE_CHECKING
from pygame import (
    SRCALPHA,
    Rect,
    Surface,
    Vector2,
    display,
    draw,
    freetype,
    mouse,
    transform,
)

if TYPE_CHECKING:
    from src.classes.input import SelectorOption
    from src.game import Game


class GridSprite(DirtySprite):
    def __init__(self, game: Game):
        super().__init__()

        self.game = game

        self.image: Surface = Surface(
            display.get_window_size(), SRCALPHA
        ).convert_alpha()
        self.rect: Rect = self.image.get_rect(topleft=(0, 0))
        self.dirty = 1
        self.visible = 1

        self.game.camera.on("move", self._redraw)
        self.game.camera.on("resize", self._on_resize)
        self.game.camera.on("zoom", self._redraw)
        self._redraw()

    def _on_resize(self):
        self.image = Surface(display.get_window_size(), SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 0))
        self._redraw()

    def _redraw(self):
        assert self.image is not None
        assert self.rect is not None

        width = self.rect.width
        height = self.rect.height

        self.image.fill((0, 0, 0, 0))

        zoom = self.game.camera.zoom
        cam_x = self.game.camera.position.x
        cam_y = self.game.camera.position.y

        first_world_x = int(cam_x // GRID_SIZE) * GRID_SIZE
        last_world_x = cam_x + (width / zoom) + GRID_SIZE
        world_x = first_world_x
        while world_x <= last_world_x:
            screen_x = int((world_x - cam_x) * zoom)
            color = (90, 90, 90, 255) if world_x == 0 else (55, 55, 55, 255)
            draw.line(self.image, color, (screen_x, 0), (screen_x, height), 1)
            world_x += GRID_SIZE

        first_world_y = int(cam_y // GRID_SIZE) * GRID_SIZE
        last_world_y = cam_y + (height / zoom) + GRID_SIZE
        world_y = first_world_y
        while world_y <= last_world_y:
            screen_y = int((world_y - cam_y) * zoom)
            color = (90, 90, 90, 255) if world_y == 0 else (55, 55, 55, 255)
            draw.line(self.image, color, (0, screen_y), (width, screen_y), 1)
            world_y += GRID_SIZE

        self.dirty = 1

    def destroy(self):
        self.game.camera.remove_listener("move", self._redraw)
        self.game.camera.remove_listener("resize", self._on_resize)
        self.game.camera.remove_listener("zoom", self._redraw)


class UI(EventEmitter, DirtySprite):
    def __init__(self, game: Game):
        EventEmitter.__init__(self)
        DirtySprite.__init__(self)

        self.game = game
        self.grid_sprite = GridSprite(game)
        self.image: Surface = Surface(
            display.get_window_size(), SRCALPHA
        ).convert_alpha()
        self.rect: Rect = self.image.get_rect(topleft=(0, 0))
        self.dirty = 1
        self.visible = 1
        if not freetype.get_init():
            freetype.init()
        self._font = freetype.SysFont("Arial", 20, bold=True)
        self._icon_font = freetype.SysFont("Arial", 10, bold=True)
        self._icon_cache: dict[str, Surface] = {}

        self.game.camera.on("resize", self._on_resize)
        self.game.on("update", self._on_update)
        self._redraw()

        self.game.sprite_layers.add(self.grid_sprite, layer=SPRITE_LAYER.GRID)
        self.game.sprite_layers.add(self, layer=SPRITE_LAYER.UI)

    def __del__(self):
        self.destroy()

    ####

    def _on_resize(self):
        self.image = Surface(display.get_window_size(), SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(topleft=(0, 0))
        self._redraw()

    def _on_update(self, _: float):
        self._redraw()

    def _selector_sprite_path(self, option: SelectorOption) -> str:
        if option.kind == "belt":
            return "assets/sprite/belt.png"

        if option.kind in ["seller", "miner"]:
            return self.game.data.get_machine_data(option.kind)["sprite"]

        if option.kind == "machine" and option.machine_type is not None:
            return self.game.data.get_machine_data(option.machine_type)["sprite"]

        return "assets/unknown.png"

    def _placeholder_icon(self, path: str, size: tuple[int, int]) -> Surface:
        icon = Surface(size, SRCALPHA).convert_alpha()
        icon.fill((255, 80, 80, 255))
        draw.rect(icon, (35, 35, 35, 255), icon.get_rect(), width=2)

        text = path.split("/")[-1]
        label, _ = self._icon_font.render(text, (20, 20, 20, 255))
        label_rect = label.get_rect(center=(size[0] // 2, size[1] // 2))
        icon.blit(label, label_rect)
        return icon

    def _get_selector_icon(
        self, option: SelectorOption, size: tuple[int, int]
    ) -> Surface:
        path = self._selector_sprite_path(option)
        cache_key = f"{path}:{size[0]}x{size[1]}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        loaded = ImageCache.get(path)
        if loaded is not None:
            icon = transform.scale(loaded, size)
        else:
            icon = self._placeholder_icon(path, size)

        self._icon_cache[cache_key] = icon
        return icon

    def _can_place_selected(
        self, selected: SelectorOption | None, grid_pos: tuple[int, int]
    ) -> bool:
        if selected is None:
            return False

        if selected.cost > self.game.data.cash:
            return False

        if grid_pos in self.game.position_map:
            for obj in self.game.position_map[grid_pos]:
                from src.objects.item import Item

                if not isinstance(obj, Item):
                    return False

        return True

    def _draw_cursor_preview(self, selected: SelectorOption | None, mode: int):
        if mode != 1 or selected is None:
            return

        mouse_pos = Vector2(mouse.get_pos())
        world_pos = self.game.camera.screen_to_world(mouse_pos)
        grid_pos = (int(world_pos.x // GRID_SIZE), int(world_pos.y // GRID_SIZE))

        world_tile = Vector2(grid_pos[0] * GRID_SIZE, grid_pos[1] * GRID_SIZE)
        screen_tile = self.game.camera.world_to_screen(world_tile)
        tile_size = max(1, int(GRID_SIZE * self.game.camera.zoom))
        tile_rect = Rect(int(screen_tile.x), int(screen_tile.y), tile_size, tile_size)

        can_place = self._can_place_selected(selected, grid_pos)
        tile_color = (70, 180, 90, 80) if can_place else (200, 70, 70, 90)
        draw.rect(self.image, tile_color, tile_rect)
        draw.rect(self.image, (220, 220, 220, 180), tile_rect, width=2)

        icon_side = max(1, tile_size - 8)
        icon_size = (icon_side, icon_side)
        base_icon = self._get_selector_icon(selected, icon_size)
        rotated_icon = transform.rotate(base_icon, self.game.input.placement_rotation)
        rotated_icon.set_alpha(180 if can_place else 130)

        icon_rect = rotated_icon.get_rect(center=tile_rect.center)
        self.image.blit(rotated_icon, icon_rect)

    def _get_hovered_machine(self) -> Machine | None:
        mouse_pos = Vector2(mouse.get_pos())
        world_pos = self.game.camera.screen_to_world(mouse_pos)
        grid_pos = (int(world_pos.x // GRID_SIZE), int(world_pos.y // GRID_SIZE))

        if grid_pos not in self.game.position_map:
            return None

        for obj in self.game.position_map[grid_pos]:
            if isinstance(obj, Machine) and not obj.destroyed:
                return obj

        return None

    def _draw_zoom_info(self):
        zoom_panel = Rect(self.rect.width - 132, 12, 120, 44)
        draw.rect(self.image, (18, 18, 18, 210), zoom_panel, border_radius=6)
        draw.rect(
            self.image, (150, 150, 150, 255), zoom_panel, width=2, border_radius=6
        )

        zoom_text, _ = self._font.render(
            f"Zoom: {self.game.camera.zoom:.2f}x", (240, 240, 240)
        )
        text_rect = zoom_text.get_rect(center=zoom_panel.center)
        self.image.blit(zoom_text, text_rect)

    def _draw_hovered_machine_info(self):
        from src.machines.miner import Miner
        from src.machines.seller import Seller

        machine = self._get_hovered_machine()
        if machine is None:
            return

        lines = [f"Position: {machine.position}"]

        if isinstance(machine, Miner):
            lines.append(f"Ore type: {machine.ore_type}")
            lines.append(f"Timer: {machine.timer}")
        elif isinstance(machine, Seller):
            pass
        else:
            lines.append(f"Timer: {machine.timer}")
            lines.append(f"Inventory: {machine.inventory}")

        panel_width = min(420, self.rect.width - 24)
        panel_x = self.rect.width - panel_width - 12
        panel_y = 64
        line_height = 18
        panel_height = 12 + (line_height * len(lines)) + 10
        info_panel = Rect(panel_x, panel_y, panel_width, panel_height)
        draw.rect(self.image, (18, 18, 18, 220), info_panel, border_radius=6)
        draw.rect(
            self.image, (110, 170, 255, 255), info_panel, width=2, border_radius=6
        )

        y = info_panel.y + 8
        for line in lines:
            text_surf, _ = self._icon_font.render(line, (230, 230, 230, 255))
            self.image.blit(text_surf, (info_panel.x + 8, y))
            y += line_height

    def _draw_debug_rects(self):

        for x in self.game.objects:
            debug_rect = x.screen_rect.copy()
            draw.rect(
                self.image,
                (0, 255, 0, 255) if x.visible else (255, 0, 0, 255),
                debug_rect,
                width=1,
            )

    def _draw_debug_belt_links(self):
        drawn_links: set[tuple[int, int]] = set()
        for x in self.game.objects:
            if not isinstance(x, Belt):
                continue

            neighbors: list[Belt] = [x.next] if x.next else []
            neighbors.extend(x.prevs)

            for neighbor in neighbors:
                x_id = id(x)
                neighbor_id = id(neighbor)
                link_key = (
                    (x_id, neighbor_id) if x_id <= neighbor_id else (neighbor_id, x_id)
                )
                if link_key in drawn_links:
                    continue
                drawn_links.add(link_key)

                a = self.game.camera.world_to_screen(x.position)
                b = self.game.camera.world_to_screen(neighbor.position)
                half_grid = (GRID_SIZE * self.game.camera.zoom) / 2

                a_line = (
                    a.x + half_grid,
                    a.y + half_grid,
                )
                b_line = (
                    b.x + half_grid,
                    b.y + half_grid,
                )

                draw.line(
                    self.image,
                    (0, 255, 0, 255),
                    a_line,
                    b_line,
                    width=1,
                )

    def _redraw(self):
        assert self.image is not None
        assert self.rect is not None

        self.image.fill((0, 0, 0, 0))

        selectors = self.game.input.selectors
        selected = self.game.input.selected_obj
        mode = self.game.input.mode

        mode_names = {
            1: "PLACE",
            2: "MOVE",
            3: "REMOVE",
        }

        mode_panel = Rect(12, 12, 230, 68)
        draw.rect(self.image, (18, 18, 18, 210), mode_panel, border_radius=6)
        draw.rect(
            self.image, (150, 150, 150, 255), mode_panel, width=2, border_radius=6
        )

        mode_text, _ = self._font.render(
            f"Mode: {mode_names.get(mode, 'UNKNOWN')}", (240, 240, 240)
        )
        cash_text, _ = self._font.render(
            f"Cash: ${int(self.game.data.cash)}", (130, 220, 130)
        )
        hint_text, _ = self._font.render("(press M to switch)", (170, 170, 170))
        self.image.blit(mode_text, (mode_panel.x + 10, mode_panel.y + 4))
        self.image.blit(cash_text, (mode_panel.x + 10, mode_panel.y + 23))
        self.image.blit(hint_text, (mode_panel.x + 10, mode_panel.y + 42))

        y = self.rect.height - 16 - GRID_SIZE
        x = 0

        for option in selectors:
            slot = Rect(x, y, GRID_SIZE, GRID_SIZE)

            bg = (35, 35, 35, 220) if mode == 1 else (20, 20, 20, 170)
            border = (
                (255, 220, 90, 255)
                if option is selected and mode == 1
                else (110, 110, 110, 230)
            )
            draw.rect(self.image, bg, slot)
            draw.rect(self.image, border, slot, width=2)

            icon_rect = slot.inflate(-22, -22)
            icon = self._get_selector_icon(option, (icon_rect.width, icon_rect.height))
            self.image.blit(icon, icon_rect)
            x += GRID_SIZE

        self._draw_cursor_preview(selected, mode)
        self._draw_zoom_info()
        self._draw_hovered_machine_info()

        if self.game.DEBUG:
            self._draw_debug_rects()
            self._draw_debug_belt_links()

        self.dirty = 1

    def destroy(self):
        self.grid_sprite.destroy()
        self.game.sprite_layers.remove(self.grid_sprite)
        self.game.sprite_layers.remove(self)
        self.game.camera.remove_listener("resize", self._on_resize)
        self.game.remove_listener("update", self._on_update)
        self.remove_all_listeners()
        self._icon_cache.clear()
