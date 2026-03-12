from __future__ import annotations

from pygame.typing import FileLike
from pygame import Surface, image
import pygame


class ImageCache:
    _cache: dict[str, Surface] = {}

    @classmethod
    def _to_cache_key(cls, file: FileLike) -> str | None:
        if isinstance(file, str):
            return file

        fspath = getattr(file, "__fspath__", None)
        if callable(fspath):
            return str(fspath())

        return None

    @classmethod
    def get(cls, file: FileLike) -> Surface | None:
        key = cls._to_cache_key(file)
        if key is not None and key in cls._cache:
            return cls._cache[key]

        try:
            loaded = image.load(file).convert_alpha()
        except (FileNotFoundError, OSError, pygame.error):
            return None

        if key is not None:
            cls._cache[key] = loaded

        return loaded

    @classmethod
    def preload(cls, paths: list[str]) -> tuple[int, int]:
        loaded_count = 0
        failed_count = 0

        for path in dict.fromkeys(paths):
            if path in cls._cache:
                continue

            try:
                cls._cache[path] = image.load(path).convert_alpha()
                loaded_count += 1
            except (FileNotFoundError, OSError, pygame.error):
                failed_count += 1

        return loaded_count, failed_count
