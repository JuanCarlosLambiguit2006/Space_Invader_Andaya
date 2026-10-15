import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets', 'images')

class Enemy:
    TYPES = [
        ('enemy_red.png', 72, 64, 1, 10),
        ('enemy_purple.png', 78, 68, 1, 12),
        ('enemy_blue.png', 82, 70, 2, 15),
        ('enemy_ice.png', 76, 82, 2, 18),
        ('enemy_gold.png', 82, 70, 2, 20),
        ('enemy_green.png', 78, 72, 3, 25),
    ]

    def __init__(self, index, total_enemies, screen_width, stage=1):
        kind = (index + max(0, stage - 1)) % len(self.TYPES)
        filename, self.width, self.height, self.hp, self.points = self.TYPES[kind]
        self.kind = kind
        self.image = pygame.image.load(os.path.join(ASSET_DIR, filename)).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (self.width, self.height))
        self.max_hp = self.hp
        self.stage = stage
        self.screen_width = screen_width

        spacing = screen_width / (total_enemies + 1)
        self.target_mid_x = spacing * (index + 1) - (self.width // 2)
        self.target_mid_y = 125 + (45 if index % 2 == 0 else 0) + (stage % 3) * 8
        self.x = self.target_mid_x
        self.y = -100 - index * 25
        self.state = 'entering'
        self.speed = 2.8 + min(3.0, stage * 0.16)
        self.dx = 0
        self.dy = 0
        self.fire_timer = (index * 17 + stage * 11) % 120
        self.fire_interval = max(34, 108 - stage * 4)
        self.fire_chance = min(0.90, 0.34 + stage * 0.035)

    def start_drop(self, target_x, target_y):
        self.state = 'dropping'
        distance_x = target_x - self.x
        distance_y = target_y - self.y
        distance = (distance_x ** 2 + distance_y ** 2) ** 0.5
        if distance > 0:
            self.dx = (distance_x / distance) * self.speed
            self.dy = (distance_y / distance) * self.speed
        else:
            self.dx = 0
            self.dy = self.speed

    def update(self):
        if self.state == 'entering':
            if self.y < self.target_mid_y:
                self.y += 2.5
            else:
                self.y = self.target_mid_y
                self.state = 'waiting'
        elif self.state == 'dropping':
            self.x += self.dx
            self.y += self.dy
            if self.y > 900 or self.x < -180 or self.x > self.screen_width + 180:
                self.state = 'offscreen'

    def update_fire_timer(self):
        if self.state != 'waiting':
            return False
        self.fire_timer += 1
        if self.fire_timer >= self.fire_interval:
            self.fire_timer = 0
            return True
        return False

    def get_fire_position(self):
        return (self.x + self.width * 0.5, self.y + self.height * 0.82)

    def hit(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.state = 'offscreen'
            return True
        return False

    def get_rect(self):
        return pygame.Rect(int(self.x + self.width * 0.12), int(self.y + self.height * 0.12),
                           int(self.width * 0.76), int(self.height * 0.76))

    def draw(self, screen):
        if self.state != 'offscreen':
            screen.blit(self.image, (int(self.x), int(self.y)))
            if self.max_hp > 1 and self.hp < self.max_hp:
                pygame.draw.rect(screen, (55, 15, 25), (int(self.x), int(self.y) - 7, self.width, 4))
                pygame.draw.rect(screen, (255, 75, 85), (int(self.x), int(self.y) - 7, int(self.width * self.hp / self.max_hp), 4))
