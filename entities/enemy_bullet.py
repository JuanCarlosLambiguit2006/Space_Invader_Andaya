import pygame

class EnemyBullet:
    """Downward energy projectile fired by regular enemies and bosses."""
    def __init__(self, x, y, vx=0, vy=5.5, damage=1, size=9, color=(255, 70, 90)):
        self.x=float(x); self.y=float(y)
        self.vx=float(vx); self.vy=float(vy)
        self.damage=damage; self.size=size; self.color=color
        self.is_active=True
        self.trail=[]

    def update(self, width, height):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5: self.trail.pop(0)
        self.x += self.vx; self.y += self.vy
        if self.y > height + 30 or self.x < -30 or self.x > width + 30:
            self.is_active=False

    def get_rect(self):
        r=self.size
        return pygame.Rect(int(self.x-r/2), int(self.y-r/2), r, r*2)

    def draw(self, screen):
        if not self.is_active: return
        for i,(tx,ty) in enumerate(self.trail):
            alpha=max(35, 150-i*22)
            s=max(2, self.size-i*2)
            surf=pygame.Surface((s*3,s*3), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (s*1.5,s*1.5), s)
            screen.blit(surf, (int(tx-s*1.5), int(ty-s*1.5)))
        pygame.draw.circle(screen, (255,240,210), (int(self.x),int(self.y)), max(2,self.size//3))
        pygame.draw.circle(screen, self.color, (int(self.x),int(self.y)), self.size//2)
