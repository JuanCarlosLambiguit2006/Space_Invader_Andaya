import pygame, math

# Pygame fallback-safe UI color. This fixes NameError: name 'WHITE' is not defined.
WHITE=(242,248,255)

COLORS={
    'gold':((255,205,70),(82,52,18)),
    'orange':((255,155,45),(91,45,15)),
    'blue':((55,175,255),(18,54,105)),
    'green':((70,245,150),(18,78,58)),
    'red':((255,75,100),(91,22,38)),
    'brown':((180,125,45),(66,40,18)),
}
FONT_NAME='dejavusansmono'

class PixelButton:
    def __init__(self,rect,label,color='gold',icon='',font_size=18):
        self.rect=pygame.Rect(rect); self.label=label; self.color=color; self.icon=icon
        self.font_size=font_size; self.hover=False; self.enabled=True
    def update(self,pos): self.hover=self.enabled and self.rect.collidepoint(pos)
    def clicked(self,pos): return self.enabled and self.rect.collidepoint(pos)
    def _poly(self,r,cut=10):
        r=pygame.Rect(r); c=min(cut,max(4,r.w//6),max(4,r.h//3))
        return [(r.x+c,r.y),(r.right-c,r.y),(r.right,r.y+c),(r.right,r.bottom-c),
                (r.right-c,r.bottom),(r.x+c,r.bottom),(r.x,r.bottom-c),(r.x,r.y+c)]
    def draw(self,surface,font=None):
        base,shadow=COLORS.get(self.color,COLORS['gold']); r=self.rect
        if self.hover:
            pulse=75+int(55*(0.5+0.5*math.sin(pygame.time.get_ticks()/120)))
            glow=pygame.Surface((r.w+30,r.h+30),pygame.SRCALPHA)
            pygame.draw.polygon(glow,(*base,pulse),self._poly(glow.get_rect(),12),4)
            surface.blit(glow,(r.x-15,r.y-15))
        pygame.draw.polygon(surface,(0,3,12),self._poly(r.move(0,7),10))
        pygame.draw.polygon(surface,shadow,self._poly(r,10))
        inner=r.inflate(-5,-5); pygame.draw.polygon(surface,(4,15,34),self._poly(inner,7))
        pygame.draw.polygon(surface,base,self._poly(inner,7),2)
        fill=inner.inflate(-5,-5); pygame.draw.polygon(surface,(7,24,49),self._poly(fill,5))
        hi=tuple(min(255,c+65) for c in base); lo=tuple(max(0,c-65) for c in base)
        pygame.draw.line(surface,hi,(inner.x+10,inner.y+2),(inner.right-12,inner.y+2),2)
        pygame.draw.line(surface,lo,(inner.x+12,inner.bottom-2),(inner.right-10,inner.bottom-2),2)
        pygame.draw.rect(surface,hi,(inner.x+10,inner.y+8,18,2)); pygame.draw.rect(surface,hi,(inner.right-28,inner.y+8,18,2))
        icon_size=min(r.height-12,40)
        icon_rect=pygame.Rect(r.right-icon_size-9,r.y+6,icon_size,icon_size) if self.icon else None
        label_right=icon_rect.left-9 if icon_rect else r.right-10
        label_area=pygame.Rect(r.left+12,r.top+6,max(20,label_right-r.left-12),r.height-12)
        f=pygame.font.SysFont(FONT_NAME,self.font_size,bold=True)
        rendered=f.render(self.label,True,WHITE if self.hover else (220,238,255))
        if rendered.get_width()>label_area.w:
            f=pygame.font.SysFont(FONT_NAME,max(10,self.font_size-2),bold=True); rendered=f.render(self.label,True,WHITE)
        surface.blit(rendered,rendered.get_rect(center=label_area.center))
        if icon_rect:
            pygame.draw.polygon(surface,(5,20,40),self._poly(icon_rect,6))
            pygame.draw.polygon(surface,hi,self._poly(icon_rect.inflate(-3,-3),4),2)
            self.draw_icon(surface,icon_rect.centerx,icon_rect.centery,self.icon,hi)
    @staticmethod
    def draw_icon(surface,x,y,icon,color=(220,245,255)):
        c=color
        if icon in ('play','right'):pygame.draw.polygon(surface,c,[(x-5,y-9),(x+7,y),(x-5,y+9)])
        elif icon=='plus':
            pygame.draw.rect(surface,c,(x-2,y-9,4,18));pygame.draw.rect(surface,c,(x-9,y-2,18,4))
        elif icon in ('x','close'):
            pygame.draw.line(surface,c,(x-7,y-7),(x+7,y+7),3);pygame.draw.line(surface,c,(x+7,y-7),(x-7,y+7),3)
        elif icon=='left':pygame.draw.polygon(surface,c,[(x+6,y-9),(x-7,y),(x+6,y+9)])
        elif icon=='up':pygame.draw.polygon(surface,c,[(x,y-9),(x-9,y+5),(x+9,y+5)])
        elif icon=='down':pygame.draw.polygon(surface,c,[(x,y+9),(x-9,y-5),(x+9,y-5)])
        elif icon=='pause':
            pygame.draw.rect(surface,c,(x-7,y-9,5,18));pygame.draw.rect(surface,c,(x+2,y-9,5,18))
        elif icon=='menu':
            for yy in (-7,0,7):pygame.draw.rect(surface,c,(x-9,y+yy,18,3))
        elif icon=='save':
            pygame.draw.rect(surface,c,(x-8,y-9,16,18),2);pygame.draw.rect(surface,c,(x-5,y-8,10,6))
        elif icon=='help':
            q=pygame.font.SysFont(FONT_NAME,17,bold=True).render('?',True,c);surface.blit(q,q.get_rect(center=(x,y)))
        elif icon=='gear':
            pygame.draw.circle(surface,c,(x,y),8,2);pygame.draw.circle(surface,c,(x,y),3)
            for a in range(0,360,45):
                rad=math.radians(a);pygame.draw.line(surface,c,(int(x+10*math.cos(rad)),int(y+10*math.sin(rad))),(int(x+13*math.cos(rad)),int(y+13*math.sin(rad))),2)

class MobileButtons:
    def __init__(self,screen_width,screen_height):
        self.screen_width=screen_width;self.screen_height=screen_height;self.visible=True
        self.left_pressed=False; self.right_pressed=False; self.fire_pressed=False
        self.layout()
    def layout(self):
        size=max(62,min(78,int(self.screen_height*0.075))); y=self.screen_height-size-24
        self.left=pygame.Rect(24,y,size,size);self.right=pygame.Rect(34+size,y,size,size)
        fire_w=max(118,min(150,int(self.screen_width*0.09)));self.fire=pygame.Rect(self.screen_width-fire_w-28,y,fire_w,size)
    def resize(self,w,h):self.screen_width=w;self.screen_height=h;self.layout()
    def set_visible(self,visible):self.visible=visible
    def draw(self,screen,font):
        if not self.visible:return
        for rect,color in ((self.left,'blue'),(self.right,'blue'),(self.fire,'red')):
            PixelButton(rect,'',color,'',font_size=14).draw(screen,font)
    def handle_mouse(self,player,events):
        if not self.visible:return False

        pos=pygame.mouse.get_pos()
        pressed=pygame.mouse.get_pressed()[0]
        self.left_pressed=pressed and self.left.collidepoint(pos)
        self.right_pressed=pressed and self.right.collidepoint(pos)
        self.fire_pressed=pressed and self.fire.collidepoint(pos)

        if self.left_pressed:player.move_left()
        if self.right_pressed:player.move_right()
        return self.fire_pressed
