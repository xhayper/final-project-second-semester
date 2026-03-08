from pygame.sprite import DirtySprite, LayeredDirty
from src.classes.sprite_object import Sprite
from pygame import Clock, event, display
from typing import TYPE_CHECKING, List
from src.classes.camera import Camera
import pygame

if TYPE_CHECKING:
    from src.classes.game_object import GameObject


class Game:
    DEBUG = True

    def __init__(self):
        self.surface = display.set_mode((1280, 720), pygame.RESIZABLE)
        self.sprite_layers: LayeredDirty[DirtySprite] = LayeredDirty(default_layer=1)
        self.camera = Camera(self)
        self.objects: List[GameObject] = []

        self.objects.append(Sprite(self, "/Users/hayper/Downloads/pixil-frame-0.png"))

        display.set_caption("Funky Factory Game")

        # stuff
        self.__requested_flip = False

    def request_flip(self):
        self.__requested_flip = True

    def start(self):
        try:
            running = True
            clock = Clock()
            dt = 0

            while running:
                events = event.get()
                self.surface.fill((0, 0, 0))

                for evt in events:
                    if evt.type == pygame.QUIT:
                        running = False
                        break

                if not running:
                    break

                # Early updating (IE: System, etc etc)
                for x in [self.camera]:
                    x.update(dt, events)

                for x in self.objects:
                    x.update(dt, events)

                for x in self.objects:
                    if self.camera.is_in_camera(x.rect):
                        x.render(self.surface)


                x = self.sprite_layers.draw(self.surface)
                if self.__requested_flip:
                    display.flip()
                    self.__requested_flip = False
                else:
                    display.update(x)

                dt = clock.tick(60) / 1000
        except KeyboardInterrupt:
            pass
