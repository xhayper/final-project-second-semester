from __future__ import annotations

from src.constants import DIRECTION, SPRITE_LAYER, GRID_SIZE, CULLING_DISABLED


def rotate_90(v: tuple[int, int]):
    x, y = v
    return (y, -x)


DIRECTION_VECTORS = {
    DIRECTION.FORWARD: (0, 1),
    DIRECTION.LEFT: (-1, 0),
    DIRECTION.BACKWARD: (0, -1),
    DIRECTION.RIGHT: (1, 0),
}

ROTATION_DIRECTION_VECTOR: dict[int, dict[DIRECTION, tuple[int, int]]] = {}

for angle in (0, 90, 180, 270):
    rotations = angle // 90
    ROTATION_DIRECTION_VECTOR[angle] = {}

    for direction, vec in DIRECTION_VECTORS.items():
        rotated = vec
        for _ in range(rotations):
            rotated = rotate_90(rotated)

        ROTATION_DIRECTION_VECTOR[angle][direction] = rotated
