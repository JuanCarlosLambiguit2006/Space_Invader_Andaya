import pygame
from managers.game_manager import GameManager

pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 832
screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.RESIZABLE)
pygame.display.set_caption("SPACE INVADERS")
game=GameManager(screen,SCREEN_WIDTH,SCREEN_HEIGHT)
clock=pygame.time.Clock()

running=True
while running:
    events=pygame.event.get()
    for event in events:
        if event.type==pygame.QUIT: running=False
        if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
            game.settings['fullscreen']=not game.settings.get('fullscreen',False)
            game.save_settings()
            flags=pygame.FULLSCREEN if game.settings['fullscreen'] else pygame.RESIZABLE
            screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),flags)
            game.screen=screen
        if event.type==pygame.VIDEORESIZE:
            SCREEN_WIDTH=max(800,event.w);SCREEN_HEIGHT=max(600,event.h)
            screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT),pygame.RESIZABLE)
            game.screen=screen;game.w=SCREEN_WIDTH;game.h=SCREEN_HEIGHT
            game.resize_background()
            game.buttons.resize(SCREEN_WIDTH,SCREEN_HEIGHT)
    game.update(events)
    pygame.display.flip()
    clock.tick(60)

game.db.disconnect()
try:
    if pygame.mixer.get_init(): pygame.mixer.music.stop()
except Exception:
    pass
pygame.quit()
