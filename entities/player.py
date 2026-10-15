import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets', 'images')

class Player:
    SHIPS = [
        {
            'name': 'NIGHT HAWK',
            'image': 'ship_black.png',
            'bullet': 'red',
            'speed': 5.2,
            'hp': 3,
            'ultimate': 'Arayko',
            'color': (255, 75, 100),
        },
        {
            'name': 'BLUE TITAN',
            'image': 'ship_blue.png',
            'bullet': 'blue',
            'speed': 4.8,
            'hp': 4,
            'ultimate': 'Tonix Gwapo',
            'color': (70, 190, 255),
        },
    ]

    def __init__(self, screen_width, screen_height, selected_ship=0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_ship = int(selected_ship) % len(self.SHIPS)
        spec = self.SHIPS[self.selected_ship]
        self.width = 96
        self.height = 110
        self.speed = spec['speed']
        self.max_hp = spec['hp']
        self.image = pygame.image.load(os.path.join(ASSET_DIR, spec['image'])).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (self.width, self.height))
        self.x = screen_width // 2 - self.width // 2
        self.y = screen_height - self.height - 24

        self.is_blinking = False
        self.blink_timer = 0
        self.visible = True

    @property
    def bullet_type(self):
        return self.SHIPS[self.selected_ship]['bullet']

    @property
    def ship_name(self):
        return self.SHIPS[self.selected_ship]['name']

    @property
    def ultimate_name(self):
        return self.SHIPS[self.selected_ship]['ultimate']

    @property
    def bullet_color(self):
        return self.SHIPS[self.selected_ship]['color']

    def move_left(self):
        if not self.is_blinking:
            self.x -= self.speed

    def move_right(self):
        if not self.is_blinking:
            self.x += self.speed

    def keep_inside_screen(self):
        self.x = max(0, min(self.x, self.screen_width - self.width))

    def get_rect(self):
        return pygame.Rect(int(self.x + 14), int(self.y + 12), self.width - 28, self.height - 22)

    def get_fire_points(self):
        cx = self.x + self.width / 2
        top = self.y + 12
        if self.selected_ship == 0:
            return [(cx - 23, top), (cx + 23, top)]
        return [(cx, top), (cx - 25, top + 8), (cx + 25, top + 8)]

    def update_blink(self):
        if self.is_blinking:
            self.blink_timer += 1
            if self.blink_timer % 10 == 0:
                self.visible = not self.visible
        else:
            self.visible = True

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, (int(self.x), int(self.y)))
