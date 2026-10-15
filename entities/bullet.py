import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets', 'images')

class Bullet:
    ASSETS = {
        'red': ('bullet_red.png', (12, 42), 13),
        'pink': ('bullet_pink.png', (12, 42), 13),
        'blue': ('bullet_blue.png', (13, 46), 14),
    }

    def __init__(self, x, y, variant='red', vx=0, damage=1, scale=1.0):
        self.variant = variant if variant in self.ASSETS else 'red'
        filename, size, speed = self.ASSETS[self.variant]
        self.width = max(6, int(size[0] * scale))
        self.height = max(10, int(size[1] * scale))
        self.image = pygame.image.load(os.path.join(ASSET_DIR, filename)).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (self.width, self.height))
        self.x = float(x - self.width / 2)
        self.y = float(y - self.height / 2)
        self.speed = speed
        self.vx = float(vx)
        self.damage = damage
        self.is_active = True

    def update(self):
        self.x += self.vx
        self.y -= self.speed
        if self.y < -self.height - 20 or self.x < -120 or self.x > 2200:
            self.is_active = False

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, (int(self.x), int(self.y)))
