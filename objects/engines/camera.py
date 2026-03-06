from objects.game_object import GameObject


class Camera(GameObject):
    def __init__(self, game):
        super().__init__(game)
        self.force_render = True
        # Decide if I want to add this or not
        self.scale = 1

    def is_in_camera_view(self, position):
        cam_x, cam_y = self.position
        view_w = self.game.screen.get_width()
        view_h = self.game.screen.get_height()
        size = self.game.SIZE_PER_TILE

        tile_left = position[0]
        tile_top = position[1]
        tile_right = tile_left + size
        tile_bottom = tile_top + size

        cam_right = cam_x + view_w
        cam_bottom = cam_y + view_h

        return not (
            tile_right < cam_x
            or tile_left > cam_right
            or tile_bottom < cam_y
            or tile_top > cam_bottom
        )

    def to_camera_position(self, position):
        cam_x, cam_y = self.position
        obj_x, obj_y = position
        return (obj_x - cam_x, obj_y - cam_y)

    def to_world_position(self, position):
        cam_x, cam_y = self.position
        obj_x, obj_y = position
        return (obj_x + cam_x, obj_y + cam_y)
