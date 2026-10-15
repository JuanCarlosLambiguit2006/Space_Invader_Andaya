import os
import math
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets', 'images')

class PowerUp:
    TYPES = {
        'SHIELD': ('reference_power_shield.png', (70,230,255)),
        'OVERDRIVE': ('reference_power_overdrive.png', (255,185,55)),
        'TRIPLE': ('reference_power_triple.png', (180,100,255)),
    }
    def __init__(self, x, y, kind):
        self.kind = kind if kind in self.TYPES else 'SHIELD'
        filename, self.color = self.TYPES[self.kind]
        self.image = pygame.image.load(os.path.join(ASSET_DIR, filename)).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (42,42))
        self.x=float(x-21); self.y=float(y-21); self.vy=1.65; self.spin=0.0; self.is_active=True

    def update(self, width, height):
        self.y += self.vy
        self.spin += 0.08
        if self.y > height + 60: self.is_active=False

    def get_rect(self):
        return pygame.Rect(int(self.x+4), int(self.y+4), 34, 34)

    def draw(self, screen):
        if not self.is_active: return
        pulse=2+int(2*(0.5+0.5*math.sin(self.spin)))
        r=pygame.Rect(int(self.x-pulse),int(self.y-pulse),42+pulse*2,42+pulse*2)
        glow=pygame.Surface((r.w,r.h),pygame.SRCALPHA)
        pygame.draw.ellipse(glow,(*self.color,70),glow.get_rect(),2)
        screen.blit(glow,(r.x,r.y))
        screen.blit(self.image,(int(self.x),int(self.y)))
