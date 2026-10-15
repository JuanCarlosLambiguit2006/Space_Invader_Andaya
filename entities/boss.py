import os
import math
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSET_DIR = os.path.join(ROOT, 'assets', 'images')

BOSS_TYPES = [
    ('GREEN TITAN', 'boss_green.png', (75, 245, 135)),
    ('VOID REAVER', 'boss_alien.png', (205, 100, 255)),
    ('SWARM QUEEN', 'boss_moth.png', (255, 95, 180)),
]

class Boss:
    def __init__(self, screen_width, screen_height, stage=1):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.stage = int(stage)
        self.type_index = (self.stage - 1) % len(BOSS_TYPES)
        self.name, filename, self.color = BOSS_TYPES[self.type_index]

        # Difficulty scales continuously with stage.
        self.width = 300 if self.type_index != 1 else 320
        self.height = 190 if self.type_index != 1 else 205
        path = os.path.join(ASSET_DIR, filename)
        self.image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (self.width, self.height))

        self.x = screen_width // 2 - self.width // 2
        self.y = -self.height - 20
        self.target_y = 62
        self.speed = 2.3 + min(2.6, self.stage * 0.13)
        self.direction = 1
        self.state = 'entering'
        self.phase = 0.0

        # Tougher but still readable HP curve.
        self.max_hp = min(160, 42 + self.stage * 8)
        self.hp = self.max_hp
        self.points = 700 + self.stage * 140

        self.fire_timer = 0
        self.fire_interval = max(24, 58 - self.stage * 2)
        self.ultimate_timer = 0
        self.ultimate_interval = max(150, 300 - self.stage * 9)
        self.ultimate_warning = 0
        self.enraged = False

    def update(self):
        self.phase += 0.045
        if self.state == 'entering':
            self.y += 2.8
            if self.y >= self.target_y:
                self.y = self.target_y
                self.state = 'active'
        elif self.state == 'active':
            # Enrage below 40% HP.
            self.enraged = self.hp <= self.max_hp * 0.40
            speed = self.speed * (1.28 if self.enraged else 1.0)
            self.x += speed * self.direction
            if self.x <= 20 or self.x + self.width >= self.screen_width - 20:
                self.direction *= -1
            self.y = self.target_y + math.sin(self.phase) * (11 if not self.enraged else 16)

    def update_fire_timer(self):
        if self.state != 'active': return False
        self.fire_timer += 1
        interval = max(18, self.fire_interval - (8 if self.enraged else 0))
        if self.fire_timer >= interval:
            self.fire_timer = 0
            return True
        return False

    def update_ultimate_timer(self):
        if self.state != 'active': return False
        self.ultimate_timer += 1
        interval = max(110, self.ultimate_interval - (45 if self.enraged else 0))
        remaining = interval - self.ultimate_timer
        if 0 < remaining <= 55:
            self.ultimate_warning = remaining
        if self.ultimate_timer >= interval:
            self.ultimate_timer = 0
            self.ultimate_warning = 0
            return True
        return False

    def get_fire_positions(self):
        cx = self.x + self.width * 0.5
        y = self.y + self.height * 0.78
        spread = min(135, 58 + self.stage * 5)
        return [(cx, y), (cx - spread, y + 5), (cx + spread, y + 5)]

    def get_ultimate_pattern(self):
        cx = self.x + self.width * 0.5
        y = self.y + self.height * 0.70
        if self.type_index == 0:
            # Green Titan: crossing laser lattice.
            return 'lattice', [(cx, y, -4.4, 6.5), (cx, y, -2.2, 7.0), (cx, y, 0, 7.5), (cx, y, 2.2, 7.0), (cx, y, 4.4, 6.5)]
        if self.type_index == 1:
            # Void Reaver: spiral / helix.
            return 'spiral', [(cx, y, math.cos(i*math.tau/10)*5.2, 5.8+math.sin(i*math.tau/10)*1.5) for i in range(10)]
        # Swarm Queen: wide radial curtain.
        return 'swarm', [(cx, y, vx, vy) for vx,vy in [(-5.2,5.2),(-4.0,6.1),(-2.8,6.7),(-1.4,7.1),(0,7.4),(1.4,7.1),(2.8,6.7),(4.0,6.1),(5.2,5.2)]]

    def hit(self, damage=1):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.state = 'defeated'
            return True
        return False

    def get_rect(self):
        return pygame.Rect(int(self.x + 30), int(self.y + 18), self.width - 60, self.height - 35)

    def draw(self, screen):
        if self.state == 'defeated': return
        # Boss aura / threat indicator.
        pulse = 35 + int(25*(0.5+0.5*math.sin(self.phase*2)))
        aura = pygame.Surface((self.width+50,self.height+50), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (*self.color, pulse), aura.get_rect(), 5)
        screen.blit(aura, (int(self.x-25), int(self.y-25)))
        screen.blit(self.image, (int(self.x), int(self.y)))

        bar_w = min(520, self.screen_width - 180)
        bar_h = 16
        bar_x = (self.screen_width - bar_w)//2
        bar_y = 235
        pygame.draw.rect(screen, (8,10,25), (bar_x-4,bar_y-4,bar_w+8,bar_h+8))
        pygame.draw.rect(screen, (65,20,55), (bar_x,bar_y,bar_w,bar_h))
        fill = int(bar_w*self.hp/max(1,self.max_hp))
        pygame.draw.rect(screen, self.color, (bar_x,bar_y,fill,bar_h))
        pygame.draw.rect(screen, (255,220,80), (bar_x,bar_y,bar_w,bar_h), 2)
        f=pygame.font.SysFont('dejavusansmono',16,bold=True)
        label=f.render(f'{self.name}  •  BOSS HP {self.hp}/{self.max_hp}',True,(242,248,255))
        screen.blit(label,(bar_x,bar_y-24))
        if self.ultimate_warning > 0:
            pulse=5 + int(5*(0.5+0.5*math.sin(self.phase*8)))
            pygame.draw.circle(screen, (255,55,85), (int(self.x+self.width/2), int(self.y+self.height*0.58)), 18+pulse, 3)
            pygame.draw.circle(screen, (255,230,90), (int(self.x+self.width/2), int(self.y+self.height*0.58)), 5+pulse//2)
            wf=pygame.font.SysFont('dejavusansmono',18,bold=True)
            msg=wf.render('WARNING  //  BOSS ULTIMATE CHARGING',True,(255,70,95))
            screen.blit(msg,msg.get_rect(center=(self.screen_width//2,bar_y+38)))
