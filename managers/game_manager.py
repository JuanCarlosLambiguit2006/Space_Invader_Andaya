import json, pygame, random, time, math
from pathlib import Path
from entities.player import Player
from entities.button import MobileButtons, PixelButton
from entities.enemy import Enemy
from entities.boss import Boss
from entities.bullet import Bullet
from entities.enemy_bullet import EnemyBullet
from database.db_manager import DatabaseManager

BG=(3,8,24)
PANEL=(9,18,45)
BLUE=(40,140,255)
CYAN=(60,235,255)

WHITE=(242,248,255)
RED=(255,65,85)
GREEN=(65,245,135)
YELLOW=(255,220,70)
PURPLE=(175,90,255)
ORANGE=(255,170,35)

# Gold colors used by the pixel UI
GOLD=(255,215,0)
GOLD_LIGHT=(255,235,120)
GOLD_DARK=(150,115,20)

ROOT=Path(__file__).resolve().parents[1]


class GameManager:
    def __init__(self,screen,w,h):
        self.screen=screen
        self.w=w
        self.h=h

        self.font=pygame.font.SysFont('dejavusansmono',30,bold=True)
        self.small=pygame.font.SysFont('dejavusansmono',20,bold=True)
        self.big=pygame.font.SysFont('dejavusansmono',64,bold=True)
        self.title_font=pygame.font.SysFont('dejavusansmono',58,bold=True)

        self.audio_ready=False
        self.sfx={}
        self.music_started=False
        self.enemy_fire_sound_timer=0

        self.particles=[]
        self.fx_flash=0
        self.fx_message=''
        self.fx_message_timer=0
        self.anim_time=0.0
        self.hover_last=None

        self.db=DatabaseManager()
        self.db_ready=self.db.connect() and self.db.create_tables()

        self.player_id=None
        self.username=''
        self.email=''

        self.login_user=''
        self.login_pass=''
        self.reg_user=''
        self.reg_pass=''
        self.reg_confirm=''

        self.selected_ship=0
        self.game_mode='CLASSIC'
        self.stage=1
        self.hp=3
        self.max_hp=3
        self.ultimate_charge=100
        self.ultimate_cooldown=0
        self.mission_complete=False
        self.boss=None
        self.boss_defeated=False

        self.login_field='username'
        self.reg_field='username'
        self.reg_extra='password'

        self.show_login_password=False
        self.show_reg_password=False
        self.show_reg_confirm=False

        self.message=''
        self.message_color=RED

        self.state='login'
        self.previous='menu'
        self.show_mobile=True
        self.paused=False
        self.score=0
        self.spawn_number=6
        self.score_saved=False

        self.leaderboard=[]
        self.player_history=[]
        self.name_input=''
        self.last_game_active=False

        self.help_scroll=0

        self.settings=self.load_settings()

        self.show_mobile=bool(
            self.settings.get('show_mobile_buttons',True)
        )

        self.animations=bool(
            self.settings.get('animations',True)
        )

        self.music_enabled=bool(
            self.settings.get('music_enabled',True)
        )

        self.sfx_enabled=bool(
            self.settings.get('sfx_enabled',True)
        )

        self.buttons=MobileButtons(w,h)
        self.buttons.set_visible(self.show_mobile)

        self.reset_game(True)

        self.stars=[
            {
                'x':random.randrange(w),
                'y':random.randrange(h),
                's':random.choice([1,1,2]),
                'v':random.uniform(.15,.7)
            }
            for _ in range(120)
        ]

        self.menu_bg,self.game_bg=self.load_backgrounds()
        self.init_audio()


    def init_audio(self):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=44100,
                    size=-16,
                    channels=2,
                    buffer=512
                )

            audio=ROOT/'assets'/'audio'

            sound_files={
                'shoot':'spaceship_bullet.wav',
                'warning':'Boss_Appear.wav',
                'ultimate':'Special_Skill.wav',
                'gameover':'die_Spaceship.wav',
                'enemy_bullet':'Boss_and_Enemy_bullet.wav',
                'click':'click.wav',
                'hit':'hit.wav',
                'explosion':'explosion.wav',
            }

            for name,filename in sound_files.items():
                path=audio/filename

                if path.exists():
                    self.sfx[name]=pygame.mixer.Sound(str(path))

            self.sfx_volume=float(
                self.settings.get('sfx_volume',0.65)
            ) if hasattr(self,'settings') else 0.65

            if not getattr(self,'sfx_enabled',True):
                self.sfx_volume=0.0

            for snd in self.sfx.values():
                snd.set_volume(self.sfx_volume)

            music=audio/'space_music.wav'

            if music.exists():
                pygame.mixer.music.load(str(music))

                pygame.mixer.music.set_volume(
                    float(
                        self.settings.get(
                            'music_volume',
                            0.28
                        )
                    )
                    if hasattr(self,'settings')
                    and getattr(self,'music_enabled',True)
                    else 0.0
                )

                if getattr(self,'music_enabled',True):
                    pygame.mixer.music.play(-1)

                self.music_started=True

            self.audio_ready=True

        except Exception:
            self.audio_ready=False


    def play_sfx(self,name,volume=1.0):
        if not self.audio_ready:
            return

        snd=self.sfx.get(name)

        if snd:
            snd.set_volume(
                max(
                    0.0,
                    min(
                        1.0,
                        self.sfx_volume*volume
                    )
                )
            )

            snd.play()


    def spawn_particles(
        self,
        x,
        y,
        count=8,
        color=CYAN,
        speed=2.5,
        size=3,
        life=30
    ):
        if not self.animations:
            return

        for _ in range(count):
            a=random.random()*math.tau
            sp=random.uniform(.5,speed)

            self.particles.append(
                {
                    'x':float(x),
                    'y':float(y),
                    'vx':math.cos(a)*sp,
                    'vy':math.sin(a)*sp,
                    'life':random.randint(
                        max(8,life//2),
                        life
                    ),
                    'max':life,
                    'size':random.uniform(1,size),
                    'color':color
                }
            )


    def update_particles(self):
        alive=[]

        for q in self.particles:
            q['x']+=q['vx']
            q['y']+=q['vy']
            q['vy']+=.025
            q['life']-=1

            if q['life']>0:
                alive.append(q)

        if not self.animations:
            self.particles=[]
            return

        self.particles=alive[-700:]

        if self.fx_flash>0:
            self.fx_flash-=1

        if self.fx_message_timer>0:
            self.fx_message_timer-=1


    def draw_particles(self):
        for q in self.particles:
            alpha=max(
                0,
                min(
                    255,
                    int(
                        255*q['life']/
                        max(1,q['max'])
                    )
                )
            )

            surf=pygame.Surface(
                (
                    int(q['size']*4+4),
                    int(q['size']*4+4)
                ),
                pygame.SRCALPHA
            )

            c=(*q['color'],alpha)

            pygame.draw.circle(
                surf,
                c,
                (
                    surf.get_width()//2,
                    surf.get_height()//2
                ),
                max(
                    1,
                    int(q['size'])
                )
            )

            self.screen.blit(
                surf,
                (
                    int(q['x']-surf.get_width()/2),
                    int(q['y']-surf.get_height()/2)
                )
            )


    def show_fx(
        self,
        msg,
        color=YELLOW,
        duration=55
    ):
        self.fx_message=msg
        self.fx_message_timer=duration


    def load_settings(self):
        p=ROOT/'settings.json'

        try:
            return json.loads(
                p.read_text(
                    encoding='utf-8'
                )
            )
        except Exception:
            return {
                'show_mobile_buttons':True,
                'fullscreen':False,
                'volume':100,
                'screen_shake':True,
                'animations':True
            }


    def save_settings(self):
        try:
            (
                ROOT/'settings.json'
            ).write_text(
                json.dumps(
                    self.settings,
                    indent=4
                ),
                encoding='utf-8'
            )
        except Exception:
            pass


    def load_backgrounds(self):
        def load(name,fallback):
            for candidate in (name,fallback):
                p=(
                    ROOT/
                    'assets'/
                    'images'/
                    'backgrounds'/
                    candidate
                )

                try:
                    img=pygame.image.load(
                        str(p)
                    ).convert()

                    return pygame.transform.smoothscale(
                        img,
                        (self.w,self.h)
                    )

                except Exception:
                    pass

            return None

        return (
            load(
                'reference_bg_vibrant.png',
                'space_bridge.jpg'
            ),
            load(
                'reference_bg_retro.png',
                'space_bridge.jpg'
            )
        )


    def resize_background(self):
        if self.menu_bg:
            self.menu_bg=pygame.transform.smoothscale(
                self.menu_bg,
                (self.w,self.h)
            )

        if self.game_bg:
            self.game_bg=pygame.transform.smoothscale(
                self.game_bg,
                (self.w,self.h)
            )


    def _cut_poly(self,r,cut=14):
        r=pygame.Rect(r)

        c=min(
            cut,
            max(4,r.w//5),
            max(4,r.h//3)
        )

        return [
            (r.x+c,r.y),
            (r.right-c,r.y),
            (r.right,r.y+c),
            (r.right,r.bottom-c),
            (r.right-c,r.bottom),
            (r.x+c,r.bottom),
            (r.x,r.bottom-c),
            (r.x,r.y+c)
        ]


    def _glow_polygon(
        self,
        points,
        color,
        alpha=45,
        width=3,
        spread=10
    ):
        if not self.animations:
            return

        minx=min(p[0] for p in points)
        maxx=max(p[0] for p in points)
        miny=min(p[1] for p in points)
        maxy=max(p[1] for p in points)

        glow=pygame.Surface(
            (
                maxx-minx+spread*2+4,
                maxy-miny+spread*2+4
            ),
            pygame.SRCALPHA
        )

        local=[
            (
                x-minx+spread,
                y-miny+spread
            )
            for x,y in points
        ]

        pulse=alpha+int(
            18*math.sin(
                self.anim_time*3.0
            )
        )

        pygame.draw.polygon(
            glow,
            (*color,max(0,min(100,pulse))),
            local,
            width
        )

        self.screen.blit(
            glow,
            (
                minx-spread,
                miny-spread
            )
        )


    def neon_box(
        self,
        rect,
        accent=CYAN,
        fill=(5,16,38),
        cut=14,
        glow=True
    ):
        r=pygame.Rect(rect)
        pts=self._cut_poly(r,cut)

        if glow:
            self._glow_polygon(
                pts,
                accent,
                38,
                4,
                10
            )

        pygame.draw.polygon(
            self.screen,
            (0,3,12),
            [
                (x,y+7)
                for x,y in pts
            ]
        )

        pygame.draw.polygon(
            self.screen,
            (4,11,29),
            pts
        )

        inner=r.inflate(-8,-8)

        pygame.draw.polygon(
            self.screen,
            fill,
            self._cut_poly(
                inner,
                max(5,cut-4)
            )
        )

        pygame.draw.polygon(
            self.screen,
            (25,67,112),
            self._cut_poly(
                inner,
                max(5,cut-4)
            ),
            1
        )

        pygame.draw.polygon(
            self.screen,
            accent,
            pts,
            2
        )

        c=min(
            34,
            r.w//5,
            r.h//2
        )

        pygame.draw.line(
            self.screen,
            accent,
            (r.x+7,r.y+2),
            (r.x+c,r.y+2),
            3
        )

        pygame.draw.line(
            self.screen,
            accent,
            (r.right-c,r.bottom-2),
            (r.right-7,r.bottom-2),
            3
        )

        return r


    def hud_box(
        self,
        rect,
        title,
        value=None,
        accent=CYAN,
        value_color=WHITE,
        title_size=13,
        value_size=22
    ):
        r=self.neon_box(
            rect,
            accent,
            (4,13,34),
            10,
            True
        )

        self.text(
            title,
            r.y+8,
            title_size,
            accent,
            False,
            r.x+15
        )

        if value is not None:
            self.text(
                value,
                r.y+29,
                value_size,
                value_color,
                False,
                r.x+15
            )

        return r


    def progress_bar(
        self,
        rect,
        value,
        maximum,
        accent=CYAN,
        back=(8,25,48)
    ):
        r=pygame.Rect(rect)

        pygame.draw.rect(
            self.screen,
            (0,4,14),
            r
        )

        pygame.draw.rect(
            self.screen,
            (31,69,105),
            r,
            1
        )

        inner=r.inflate(-4,-4)

        pygame.draw.rect(
            self.screen,
            back,
            inner
        )

        ratio=(
            0
            if maximum<=0
            else max(
                0,
                min(
                    1,
                    float(value)/float(maximum)
                )
            )
        )

        fill=pygame.Rect(
            inner.x,
            inner.y,
            max(
                1,
                int(inner.w*ratio)
            ),
            inner.h
        )

        if ratio>0:
            pygame.draw.rect(
                self.screen,
                accent,
                fill
            )

            pygame.draw.rect(
                self.screen,
                tuple(
                    min(
                        255,
                        c+55
                    )
                    for c in accent
                ),
                (
                    fill.x,
                    fill.y,
                    fill.w,
                    2
                )
            )

        return r


    def text(
        self,
        msg,
        y,
        size=None,
        color=WHITE,
        center=True,
        x=None
    ):
        f=(
            self.font
            if size is None
            else pygame.font.SysFont(
                'dejavusansmono',
                size,
                bold=True
            )
        )

        t=f.render(
            str(msg),
            True,
            color
        )

        px=(
            (self.w-t.get_width())//2
            if center
            else (
                20
                if x is None
                else x
            )
        )

        self.screen.blit(
            t,
            (px,y)
        )

        return t


    def pixel_button(
        self,
        rect,
        label,
        color='blue',
        icon='',
        size=18
    ):
        return PixelButton(
            rect,
            label,
            color,
            icon,
            size
        )


    def draw_pixel_button(self,b):
        b.update(
            pygame.mouse.get_pos()
        )

        b.draw(
            self.screen,
            self.small
        )

        return b


    def draw_bg(
        self,
        reference=False,
        darken=0
    ):
        bg_image=(
            self.menu_bg
            if reference
            else self.game_bg
        )

        if bg_image:
            self.screen.blit(
                pygame.transform.smoothscale(
                    bg_image,
                    (self.w,self.h)
                ),
                (0,0)
            )

            overlay=pygame.Surface(
                (self.w,self.h),
                pygame.SRCALPHA
            )

            overlay.fill(
                (
                    3,
                    9,
                    24,
                    min(
                        220,
                        88+darken
                    )
                )
            )

            self.screen.blit(
                overlay,
                (0,0)
            )

        else:
            self.screen.fill(BG)

        if self.animations:
            scan=pygame.Surface(
                (self.w,self.h),
                pygame.SRCALPHA
            )

            for yy in range(
                0,
                self.h,
                10
            ):
                pygame.draw.line(
                    scan,
                    (60,210,255,8),
                    (0,yy),
                    (self.w,yy),
                    1
                )

            self.screen.blit(
                scan,
                (0,0)
            )

        self.draw_particles()


    def panel(self,rect):
        r=pygame.Rect(rect)

        self.neon_box(
            r,
            CYAN,
            (5,13,32),
            18,
            True
        )

        inner=r.inflate(
            -22,
            -22
        )

        pygame.draw.line(
            self.screen,
            (20,75,125),
            (inner.x+15,inner.y),
            (inner.right-15,inner.y),
            1
        )

        pygame.draw.line(
            self.screen,
            (20,75,125),
            (inner.x+15,inner.bottom),
            (inner.right-15,inner.bottom),
            1
        )

        for off in (18,32,46):
            pygame.draw.rect(
                self.screen,
                (28,115,180),
                (
                    r.x+18+off,
                    r.y+8,
                    18,
                    2
                )
            )

        for off in (18,34,50):
            pygame.draw.rect(
                self.screen,
                (25,80,135),
                (
                    r.right-70+off,
                    r.bottom-10,
                    10,
                    2
                )
            )

        return r


    def glass_panel(
        self,
        rect,
        fill_alpha=145,
        radius=28
    ):
        r=pygame.Rect(rect)
        backdrop=self.screen.subsurface(r).copy()
        thumbnail=pygame.transform.smoothscale(
            backdrop,
            (
                max(1,r.w//14),
                max(1,r.h//14)
            )
        )
        glass=pygame.transform.smoothscale(
            thumbnail,
            r.size
        ).convert_alpha()

        mask=pygame.Surface(
            r.size,
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            mask,
            (255,255,255,255),
            mask.get_rect(),
            border_radius=radius
        )
        glass.blit(
            mask,
            (0,0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        tint=pygame.Surface(
            r.size,
            pygame.SRCALPHA
        )
        pygame.draw.rect(
            tint,
            (5,17,52,fill_alpha),
            tint.get_rect(),
            border_radius=radius
        )
        glass.blit(
            tint,
            (0,0)
        )

        pygame.draw.rect(
            glass,
            (85,220,255,225),
            glass.get_rect(),
            2,
            border_radius=radius
        )
        pygame.draw.line(
            glass,
            (190,245,255,145),
            (radius+12,3),
            (glass.get_width()//2,3),
            2
        )
        pygame.draw.line(
            glass,
            (190,100,255,210),
            (glass.get_width()//2,glass.get_height()-3),
            (glass.get_width()-radius-12,glass.get_height()-3),
            2
        )

        self.screen.blit(
            glass,
            r.topleft
        )


    def input_box(
        self,
        rect,
        label,
        value,
        active=False,
        masked=False,
        show_toggle=False,
        field_icon=None
    ):
        r=pygame.Rect(rect)

        accent=(
            CYAN
            if active
            else (45,105,160)
        )

        self.neon_box(
            r,
            accent,
            (3,12,30),
            8,
            active
        )

        # -----------------------------------------------------
        # PIXEL AUTHENTICATION ICON
        # -----------------------------------------------------
        if field_icon:
            self.draw_auth_icon(
                self.screen,
                r.x+28,
                r.centery,
                field_icon,
                accent
            )

        # -----------------------------------------------------
        # LABEL
        # -----------------------------------------------------
        ftag=pygame.font.SysFont(
            'dejavusansmono',
            11,
            bold=True
        )

        label_x=(
            r.x+50
            if field_icon
            else r.x+12
        )

        tag=pygame.Rect(
            label_x,
            r.y+7,
            min(
                150,
                max(
                    90,
                    r.w//3
                )
            ),
            18
        )

        tag_text=ftag.render(
            label,
            True,
            accent
        )

        self.screen.blit(
            tag_text,
            tag_text.get_rect(
                midleft=(
                    tag.x,
                    tag.centery
                )
            )
        )

        # -----------------------------------------------------
        # VALUE
        # -----------------------------------------------------
        shown=(
            '•'*len(value)
            if masked
            else value
        )

        if not shown:
            shown='ENTER TEXT'

        text_x=(
            r.x+50
            if field_icon
            else r.x+18
        )

        text_area=pygame.Rect(
            text_x,
            r.y+29,
            r.w-(
                105
                if show_toggle
                else (
                    65
                    if field_icon
                    else 32
                )
            ),
            r.h-34
        )

        vf=pygame.font.SysFont(
            'dejavusansmono',
            18,
            bold=True
        )

        vs=vf.render(
            shown,
            True,
            WHITE if value else (110,145,175)
        )

        self.screen.blit(
            vs,
            (
                text_area.x,
                text_area.y
            )
        )

        # -----------------------------------------------------
        # CURSOR
        # -----------------------------------------------------
        if (
            active
            and self.animations
            and (
                pygame.time.get_ticks()//500
            )%2==0
        ):
            cx=(
                text_area.x+
                vs.get_width()+
                3
            )

            if cx<text_area.right-2:
                pygame.draw.rect(
                    self.screen,
                    CYAN,
                    (
                        cx,
                        text_area.y,
                        2,
                        20
                    )
                )

        # -----------------------------------------------------
        # EYE BUTTON
        # -----------------------------------------------------
        if show_toggle:
            ex=pygame.Rect(
                r.right-50,
                r.y+9,
                36,
                36
            )

            pygame.draw.rect(
                self.screen,
                (5,24,48),
                ex
            )

            pygame.draw.rect(
                self.screen,
                accent,
                ex,
                1
            )

            cx,cy=ex.center

            pygame.draw.ellipse(
                self.screen,
                WHITE,
                (
                    cx-11,
                    cy-7,
                    22,
                    14
                ),
                2
            )

            pygame.draw.circle(
                self.screen,
                WHITE,
                (cx,cy),
                3
            )


    @staticmethod
    def draw_auth_icon(
        surface,
        x,
        y,
        icon,
        color
    ):
        c=color

        # -----------------------------------------------------
        # USER / PROFILE
        # -----------------------------------------------------
        if icon=='user':
            pygame.draw.circle(
                surface,
                c,
                (x,y-7),
                5,
                2
            )

            pygame.draw.arc(
                surface,
                c,
                (
                    x-11,
                    y-1,
                    22,
                    17
                ),
                math.radians(190),
                math.radians(350),
                2
            )

        # -----------------------------------------------------
        # LOCK
        # -----------------------------------------------------
        elif icon=='lock':
            pygame.draw.arc(
                surface,
                c,
                (
                    x-7,
                    y-11,
                    14,
                    15
                ),
                math.radians(180),
                math.radians(360),
                3
            )

            pygame.draw.rect(
                surface,
                c,
                (
                    x-9,
                    y-2,
                    18,
                    13
                ),
                2
            )

            pygame.draw.circle(
                surface,
                c,
                (x,y+3),
                2
            )

            pygame.draw.line(
                surface,
                c,
                (x,y+5),
                (x,y+8),
                2
            )

        # -----------------------------------------------------
        # SHIELD + CHECK
        # -----------------------------------------------------
        elif icon=='shield':
            pts=[
                (x,y-11),
                (x+10,y-7),
                (x+8,y+4),
                (x,y+12),
                (x-8,y+4),
                (x-10,y-7)
            ]

            pygame.draw.polygon(
                surface,
                c,
                pts,
                2
            )

            pygame.draw.line(
                surface,
                c,
                (x-5,y),
                (x-1,y+4),
                2
            )

            pygame.draw.line(
                surface,
                c,
                (x-1,y+4),
                (x+6,y-4),
                2
            )


    def reset_game(self,keep_state=False):
        self.player=Player(
            self.w,
            self.h,
            self.selected_ship
        )

        self.buttons=MobileButtons(
            self.w,
            self.h
        )

        self.buttons.set_visible(
            self.show_mobile
        )

        self.bullets=[]
        self.enemy_bullets=[]

        self.fire_cooldown=0
        self.space_fire_latched=False
        self.space_fire_sound_timer=0
        self.enemy_fire_sound_timer=0

        self.enemies=[]
        self.score=0
        self.spawn_number=6
        self.score_saved=False
        self.timer=0
        self.state_timer=0
        self.stage=1

        self.max_hp=self.player.max_hp
        self.hp=self.max_hp

        self.ultimate_charge=100
        self.ultimate_cooldown=0
        self.mission_complete=False
        self.player_history=[]
        self.boss=None
        self.boss_defeated=False

        self.spawn_enemies()
        self.last_game_active=True

        if not keep_state:
            self.state='playing'


    def spawn_enemies(self):
        self.boss=None
        self.boss_defeated=False

        # Bosses appear every 3 waves:
        # 3, 6, 9, 12, ...
        #
        # BOSS RUSH still keeps its special behavior.
        if (
            self.game_mode=='BOSS RUSH'
            or self.stage%3==0
        ):
            self.boss=Boss(
                self.w,
                self.h,
                self.stage
            )

            self.enemies=[]

            self.play_sfx(
                'warning',
                0.95
            )

            self.fx_flash=6

            self.show_fx(
                f'{self.boss.name} INCOMING',
                self.boss.color,
                48
            )

        else:
            self.enemies=[
                Enemy(
                    i,
                    self.spawn_number,
                    self.w,
                    self.stage
                )
                for i in range(
                    self.spawn_number
                )
            ]

        self.timer=0


    def save_current_game(self):
        data={
            'username':self.username,
            'score':self.score,
            'spawn_number':self.spawn_number,
            'saved_at':time.time()
        }

        try:
            (
                ROOT/'savegame.json'
            ).write_text(
                json.dumps(
                    data,
                    indent=4
                ),
                encoding='utf-8'
            )

            self.message='GAME SAVED'
            self.message_color=GREEN

        except Exception:
            self.message='Could not save the game.'
            self.message_color=RED


    def load_game(self):
        try:
            data=json.loads(
                (
                    ROOT/'savegame.json'
                ).read_text(
                    encoding='utf-8'
                )
            )

            self.reset_game()

            self.score=int(
                data.get(
                    'score',
                    0
                )
            )

            self.spawn_number=max(
                5,
                int(
                    data.get(
                        'spawn_number',
                        5
                    )
                )
            )

            self.spawn_enemies()
            self.state='playing'
            self.message='GAME LOADED'
            self.message_color=GREEN

        except Exception:
            self.message='No saved game found.'
            self.message_color=RED


    # =========================================================
    # AUTHENTICATION
    # =========================================================

    def auth_geometry(
        self,
        height=590,
        register=False
    ):
        panel_w=min(
            720,
            max(
                560,
                self.w-90
            )
        )

        x=(self.w-panel_w)//2
        y=max(
            35,
            (self.h-height)//2
        )

        box_x=x+70
        box_w=panel_w-140

        if register:
            username_box=pygame.Rect(
                box_x,
                y+145,
                box_w,
                58
            )

            password_box=pygame.Rect(
                box_x,
                y+215,
                box_w,
                58
            )

            confirm_box=pygame.Rect(
                box_x,
                y+285,
                box_w,
                58
            )

            eye_rect=pygame.Rect(
                password_box.right-50,
                password_box.y+9,
                36,
                36
            )

            confirm_eye=pygame.Rect(
                confirm_box.right-50,
                confirm_box.y+9,
                36,
                36
            )

            return (
                x,
                y,
                panel_w,
                username_box,
                password_box,
                eye_rect,
                confirm_box,
                confirm_eye
            )

        username_box=pygame.Rect(
            box_x,
            y+160,
            box_w,
            62
        )

        password_box=pygame.Rect(
            box_x,
            y+238,
            box_w,
            62
        )

        eye_rect=pygame.Rect(
            password_box.right-50,
            password_box.y+9,
            36,
            36
        )

        return (
            x,
            y,
            panel_w,
            username_box,
            password_box,
            eye_rect
        )


    def handle_login(self,events):
        (
            _,
            y,
            pw,
            username_box,
            password_box,
            eye_rect
        )=self.auth_geometry(590)

        x=(self.w-pw)//2

        login_rect=pygame.Rect(
            x+90,
            y+330,
            pw-180,
            60
        )

        reg_rect=pygame.Rect(
            x+90,
            y+405,
            (pw-205)//2,
            52
        )

        exit_rect=pygame.Rect(
            reg_rect.right+25,
            y+405,
            reg_rect.w,
            52
        )

        for e in events:
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_TAB:
                    self.login_field=(
                        'password'
                        if self.login_field=='username'
                        else 'username'
                    )

                elif e.key==pygame.K_BACKSPACE:
                    if self.login_field=='username':
                        self.login_user=self.login_user[:-1]
                    else:
                        self.login_pass=self.login_pass[:-1]

                elif e.key==pygame.K_RETURN:
                    self.do_login()

                elif e.unicode.isprintable():
                    if (
                        self.login_field=='username'
                        and len(self.login_user)<24
                    ):
                        self.login_user+=e.unicode

                    elif (
                        self.login_field=='password'
                        and len(self.login_pass)<40
                    ):
                        self.login_pass+=e.unicode

            elif (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
            ):
                self.play_sfx(
                    'click',
                    0.45
                )

                if eye_rect.collidepoint(e.pos):
                    self.show_login_password=(
                        not self.show_login_password
                    )

                elif username_box.collidepoint(e.pos):
                    self.login_field='username'

                elif password_box.collidepoint(e.pos):
                    self.login_field='password'

                elif login_rect.collidepoint(e.pos):
                    self.do_login()

                elif reg_rect.collidepoint(e.pos):
                    self.state='register'
                    self.message=''

                elif exit_rect.collidepoint(e.pos):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.QUIT
                        )
                    )


    def do_login(self):
        if not self.db_ready:
            self.db_ready=(
                self.db.connect()
                and self.db.create_tables()
            )

        if not self.db_ready:
            self.message=(
                'DATABASE OFFLINE - CHECK XAMPP'
            )
            self.message_color=RED
            return

        row,msg=self.db.login_player(
            self.login_user.strip(),
            self.login_pass
        )

        if row:
            self.player_id=row['player_id']
            self.username=row['username']
            self.email=row.get('email') or ''
            self.selected_ship=int(
                row.get('selected_ship') or 0
            )

            self.state='menu'
            self.message=''
            self.login_pass=''

        else:
            self.message=msg
            self.message_color=RED


    def handle_register(self,events):
        (
            x,
            y,
            pw,
            username_box,
            password_box,
            eye_rect,
            confirm_box,
            confirm_eye
        )=self.auth_geometry(
            610,
            True
        )

        create_rect=pygame.Rect(
            x+90,
            y+370,
            (pw-205)//2,
            54
        )

        back_rect=pygame.Rect(
            create_rect.right+25,
            y+370,
            create_rect.w,
            54
        )

        for e in events:
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    self.state='login'
                    return

                if e.key==pygame.K_TAB:
                    order=[
                        'username',
                        'password',
                        'confirm'
                    ]

                    self.reg_field=order[
                        (
                            order.index(
                                self.reg_field
                            )+1
                        )%3
                    ]

                elif e.key==pygame.K_RETURN:
                    self.create_account()

                elif e.key==pygame.K_BACKSPACE:
                    attr={
                        'username':'reg_user',
                        'password':'reg_pass',
                        'confirm':'reg_confirm'
                    }[self.reg_field]

                    setattr(
                        self,
                        attr,
                        getattr(
                            self,
                            attr
                        )[:-1]
                    )

                elif e.unicode.isprintable():
                    attr={
                        'username':'reg_user',
                        'password':'reg_pass',
                        'confirm':'reg_confirm'
                    }[self.reg_field]

                    v=getattr(
                        self,
                        attr
                    )

                    limit=(
                        24
                        if self.reg_field=='username'
                        else 40
                    )

                    if len(v)<limit:
                        setattr(
                            self,
                            attr,
                            v+e.unicode
                        )

            elif (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
            ):
                self.play_sfx(
                    'click',
                    0.45
                )

                if eye_rect.collidepoint(e.pos):
                    self.show_reg_password=(
                        not self.show_reg_password
                    )

                elif confirm_eye.collidepoint(e.pos):
                    self.show_reg_confirm=(
                        not self.show_reg_confirm
                    )

                elif username_box.collidepoint(e.pos):
                    self.reg_field='username'

                elif password_box.collidepoint(e.pos):
                    self.reg_field='password'

                elif confirm_box.collidepoint(e.pos):
                    self.reg_field='confirm'

                elif create_rect.collidepoint(e.pos):
                    self.create_account()

                elif back_rect.collidepoint(e.pos):
                    self.state='login'


    def create_account(self):
        if not self.db_ready:
            self.db_ready=(
                self.db.connect()
                and self.db.create_tables()
            )

        if not self.db_ready:
            self.message=(
                'DATABASE OFFLINE - CHECK XAMPP'
            )
            self.message_color=RED
            return

        if self.reg_pass!=self.reg_confirm:
            self.message='PASSWORDS DO NOT MATCH'
            self.message_color=RED
            return

        pid,msg=self.db.register_player(
            self.reg_user.strip(),
            self.reg_pass,
            None
        )

        if pid:
            self.player_id=pid
            self.username=self.reg_user.strip()
            self.email=''
            self.reg_pass=''
            self.reg_confirm=''
            self.state='menu'
            self.message='ACCOUNT CREATED'
            self.message_color=GREEN

        else:
            self.message=msg
            self.message_color=RED


    # =========================================================
    # MAIN MENU
    # =========================================================

    def menu_layout(self):
        bw=min(
            520,
            max(
                390,
                self.w-260
            )
        )

        bh=56
        gap=10

        x=(self.w-bw)//2

        top=max(
            210,
            min(
                300,
                int(self.h*0.25)
            )
        )

        rows=[
            ('START','gold','play'),
            ('SHIP','gold','right'),
            ('LEADERBOARD','gold','right'),
            ('OPTIONS','orange','gear'),
            ('HELP','orange','help'),
            ('EXIT','red','x'),
        ]

        return [
            (
                pygame.Rect(
                    x,
                    top+i*(bh+gap),
                    bw,
                    bh
                ),
                label,
                c,
                icon
            )
            for i,(label,c,icon)
            in enumerate(rows)
        ]


    def account_layout(self):
        bw=190
        bh=48
        gap=14

        labels=[
            ('PROFILE','gold','right'),
            ('LEADERBOARD','gold','right'),
            ('LOG OUT','red','x')
        ]

        total=bw*3+gap*2

        x=max(
            20,
            (self.w-total)//2
        )

        y=self.h-72

        return [
            (
                pygame.Rect(
                    x+i*(bw+gap),
                    y,
                    bw,
                    bh
                ),
                label,
                c,
                icon
            )
            for i,(label,c,icon)
            in enumerate(labels)
        ]


    def draw_menu(self):
        # =====================================================
        # MAIN MENU
        #
        # IMPORTANT:
        # MODE / BOSS RUSH / STAGE / STATUS boxes are removed.
        # The main menu now shows only the clean reference UI.
        # =====================================================

        self.draw_bg(
            True,
            18
        )

        fw=min(
            820,
            self.w-90
        )

        fh=min(
            760,
            self.h-60
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                20,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'SPACE INVADERS',
            frame.y+30,
            50,
            CYAN
        )

        pilot_name=(
            self.username.upper()
            if self.username
            else 'PILOT'
        )

        self.text(
            f'PILOT  //  {pilot_name}',
            frame.y+96,
            14,
            GREEN
        )

        self.text(
            'MISSION CONTROL',
            frame.y+122,
            11,
            (135,190,225)
        )

        pygame.draw.rect(
            self.screen,
            (20,77,125),
            (
                frame.x+50,
                frame.y+148,
                frame.w-100,
                2
            )
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            (
                frame.x+50,
                frame.y+148,
                180,
                3
            )
        )

        # NO MODE BOX
        # NO BOSS RUSH BOX
        # NO STAGE BOX
        # NO STATUS BOX

        for rect,label,c,icon in self.menu_layout():
            self.draw_pixel_button(
                self.pixel_button(
                    rect,
                    label,
                    c,
                    icon,
                    19
                )
            )

        for rect,label,c,icon in self.account_layout():
            self.draw_pixel_button(
                self.pixel_button(
                    rect,
                    label,
                    c,
                    icon,
                    14
                )
            )


    def menu_event(self,events):
        for e in events:
            if (
                e.type!=pygame.MOUSEBUTTONDOWN
                or e.button!=1
            ):
                continue

            for rect,label,c,icon in self.menu_layout():
                if rect.collidepoint(e.pos):
                    self.play_sfx(
                        'click',
                        0.7
                    )

                    if label=='START':
                        self.state='mode_select'

                    elif label=='SHIP':
                        self.state='ship'

                    elif label=='LEADERBOARD':
                        self.state='leaderboard'

                    elif label=='OPTIONS':
                        self.state='settings'

                    elif label=='HELP':
                        self.open_help()

                    elif label=='EXIT':
                        pygame.event.post(
                            pygame.event.Event(
                                pygame.QUIT
                            )
                        )

                    return

            for rect,label,c,icon in self.account_layout():
                if rect.collidepoint(e.pos):
                    self.play_sfx(
                        'click',
                        0.7
                    )

                    if label=='PROFILE':
                        self.state='profile'

                    elif label=='LEADERBOARD':
                        self.state='leaderboard'

                    else:
                        self.player_id=None
                        self.username=''
                        self.email=''
                        self.state='login'

                    return


    def state_to_menu(self):
        self.state='menu'
        self.message=''


    def continue_game(self):
        if self.last_game_active:
            self.state='playing'
        else:
            self.reset_game()


    def pause_from_menu(self):
        if self.last_game_active:
            self.state='paused'


    def open_help(self):
        self.state='help'
        self.help_scroll=0


    def open_settings(self):
        self.state='settings'


    def settings_event(self,events):
        fw=min(
            820,
            self.w-90
        )

        fh=min(
            720,
            self.h-70
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                30,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        bx=frame.x+70
        bw=frame.w-140
        y=frame.y+165

        rows=[
            (
                pygame.Rect(
                    bx,
                    y,
                    bw,
                    62
                ),
                'mobile'
            ),
            (
                pygame.Rect(
                    bx,
                    y+78,
                    bw,
                    62
                ),
                'music'
            ),
            (
                pygame.Rect(
                    bx,
                    y+156,
                    bw,
                    62
                ),
                'sfx'
            ),
            (
                pygame.Rect(
                    bx,
                    y+234,
                    bw,
                    62
                ),
                'animations'
            ),
            (
                pygame.Rect(
                    frame.centerx-150,
                    frame.bottom-66,
                    300,
                    50
                ),
                'back'
            )
        ]

        for e in events:
            if (
                e.type==pygame.KEYDOWN
                and e.key==pygame.K_ESCAPE
            ):
                self.state='menu'
                return

            if (
                e.type!=pygame.MOUSEBUTTONDOWN
                or e.button!=1
            ):
                continue

            for rect,action in rows:
                if rect.collidepoint(e.pos):
                    self.play_sfx(
                        'click',
                        0.7
                    )

                    if action=='mobile':
                        self.show_mobile=not self.show_mobile
                        self.buttons.set_visible(
                            self.show_mobile
                        )
                        self.settings[
                            'show_mobile_buttons'
                        ]=self.show_mobile

                    elif action=='music':
                        self.music_enabled=not self.music_enabled
                        self.settings[
                            'music_enabled'
                        ]=self.music_enabled

                        if (
                            self.music_enabled
                            and self.audio_ready
                        ):
                            pygame.mixer.music.set_volume(
                                float(
                                    self.settings.get(
                                        'music_volume',
                                        0.28
                                    )
                                )
                            )

                            pygame.mixer.music.play(
                                -1
                            )

                        elif self.audio_ready:
                            pygame.mixer.music.stop()

                    elif action=='sfx':
                        self.sfx_enabled=not self.sfx_enabled

                        self.settings[
                            'sfx_enabled'
                        ]=self.sfx_enabled

                        self.sfx_volume=float(
                            self.settings.get(
                                'sfx_volume',
                                0.65
                            )
                        ) if self.sfx_enabled else 0.0

                        if self.audio_ready:
                            for snd in self.sfx.values():
                                snd.set_volume(
                                    self.sfx_volume
                                )

                    elif action=='animations':
                        self.animations=not self.animations

                        self.settings[
                            'animations'
                        ]=self.animations

                        if not self.animations:
                            self.particles=[]

                    elif action=='back':
                        self.state='menu'

                    self.save_settings()
                    return


    def update(self,events):
        self.anim_time+=1/60
        self.update_particles()

        if self.state=='login':
            self.draw_login(events)
            return

        if self.state=='register':
            self.draw_register(events)
            return

        if self.state=='menu':
            self.menu_event(events)
            self.draw_menu()
            return

        if self.state=='mode_select':
            self.mode_event(events)
            self.draw_mode_select()
            return

        if self.state=='ship':
            self.ship_event(events)
            self.draw_ship()
            return

        if self.state=='settings':
            self.settings_event(events)
            self.draw_settings()
            return

        if self.state=='help':
            self.draw_help(events)
            return

        if self.state=='leaderboard':
            self.draw_leaderboard(events)
            return

        if self.state=='profile':
            self.draw_profile(events)
            return

        if self.state=='playing':
            self.update_play(events)

        elif self.state=='paused':
            self.draw_pause(events)

        elif self.state=='blinking':
            self.update_blink()

        elif self.state=='game_over':
            self.draw_game_over(events)


    def auth_panel(
        self,
        title,
        subtitle,
        height=540
    ):
        panel_w=min(
            720,
            max(
                560,
                self.w-90
            )
        )

        x=(self.w-panel_w)//2

        y=max(
            35,
            (self.h-height)//2
        )

        self.panel(
            (
                x,
                y,
                panel_w,
                height
            )
        )

        self.text(
            title,
            y+34,
            42,
            CYAN
        )

        self.text(
            subtitle,
            y+91,
            16,
            YELLOW
        )

        pygame.draw.rect(
            self.screen,
            (20,72,120),
            (
                x+45,
                y+122,
                panel_w-90,
                2
            )
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            (
                x+45,
                y+122,
                145,
                3
            )
        )

        for i,c in enumerate(
            (
                GREEN,
                CYAN,
                GOLD_LIGHT
            )
        ):
            pygame.draw.rect(
                self.screen,
                c,
                (
                    x+46+i*18,
                    y+136,
                    10,
                    4
                )
            )

        return (
            x,
            y,
            panel_w,
            height
        )


    def draw_login(self,events):
        self.handle_login(events)
        self.draw_bg(
            True,
            30
        )

        x,y,pw,ph=self.auth_panel(
            'SPACE INVADERS',
            'PLAYER LOGIN',
            590
        )

        box_x=x+70
        box_w=pw-140

        self.input_box(
            (
                box_x,
                y+160,
                box_w,
                62
            ),
            'USERNAME',
            self.login_user,
            self.login_field=='username',
            False,
            False,
            'user'
        )

        self.input_box(
            (
                box_x,
                y+238,
                box_w,
                62
            ),
            'PASSWORD',
            self.login_pass,
            self.login_field=='password',
            not self.show_login_password,
            True,
            'lock'
        )

        login_rect=pygame.Rect(
            x+90,
            y+330,
            pw-180,
            60
        )

        reg_rect=pygame.Rect(
            x+90,
            y+405,
            (pw-205)//2,
            52
        )

        exit_rect=pygame.Rect(
            reg_rect.right+25,
            y+405,
            reg_rect.w,
            52
        )

        for rect,label,c,icon,size in [
            (
                login_rect,
                'LOGIN',
                'green',
                'play',
                20
            ),
            (
                reg_rect,
                'REGISTER',
                'blue',
                'plus',
                17
            ),
            (
                exit_rect,
                'EXIT',
                'red',
                'x',
                17
            )
        ]:
            self.draw_pixel_button(
                self.pixel_button(
                    rect,
                    label,
                    c,
                    icon,
                    size
                )
            )

        self.text(
            '',
            y+477,
            12,
            (150,190,220)
        )

        if self.message:
            self.text(
                self.message,
                y+515,
                14,
                self.message_color
            )


    def draw_register(self,events):
        self.handle_register(events)
        self.draw_bg(
            True,
            35
        )

        x,y,pw,ph=self.auth_panel(
            'CREATE ACCOUNT',
            'NEW ACCOUNT REGISTRATION',
            610
        )

        box_x=x+70
        box_w=pw-140

        self.input_box(
            (
                box_x,
                y+145,
                box_w,
                58
            ),
            'USERNAME',
            self.reg_user,
            self.reg_field=='username',
            False,
            False,
            'user'
        )

        self.input_box(
            (
                box_x,
                y+215,
                box_w,
                58
            ),
            'PASSWORD',
            self.reg_pass,
            self.reg_field=='password',
            not self.show_reg_password,
            True,
            'lock'
        )

        confirm_box=pygame.Rect(
            box_x,
            y+285,
            box_w,
            58
        )

        self.input_box(
            confirm_box,
            'CONFIRM PASSWORD',
            self.reg_confirm,
            self.reg_field=='confirm',
            not self.show_reg_confirm,
            True,
            'shield'
        )

        create_rect=pygame.Rect(
            x+90,
            y+370,
            (pw-205)//2,
            54
        )

        back_rect=pygame.Rect(
            create_rect.right+25,
            y+370,
            create_rect.w,
            54
        )

        for rect,label,c,icon in [
            (
                create_rect,
                'CREATE',
                'green',
                'plus'
            ),
            (
                back_rect,
                'BACK',
                'red',
                'left'
            )
        ]:
            self.draw_pixel_button(
                self.pixel_button(
                    rect,
                    label,
                    c,
                    icon,
                    17
                )
            )

        self.text(
            '',
            y+452,
            12,
            (150,190,220)
        )

        if self.message:
            self.text(
                self.message,
                y+490,
                14,
                self.message_color
            )


    # =========================================================
    # MISSION SELECT
    # =========================================================

    def mode_event(self,events):
        pw=min(
            780,
            self.w-90
        )

        ph=min(
            650,
            self.h-90
        )

        frame=pygame.Rect(
            (self.w-pw)//2,
            max(
                35,
                (self.h-ph)//2
            ),
            pw,
            ph
        )

        bw=min(
            500,
            frame.w-130
        )

        bh=60

        x=frame.centerx-bw//2

        buttons=[
            (
                'CLASSIC',
                pygame.Rect(
                    x,
                    frame.y+165,
                    bw,
                    bh
                )
            ),
            (
                'SURVIVAL',
                pygame.Rect(
                    x,
                    frame.y+239,
                    bw,
                    bh
                )
            ),
            (
                'BOSS RUSH',
                pygame.Rect(
                    x,
                    frame.y+313,
                    bw,
                    bh
                )
            ),
            (
                'BACK',
                pygame.Rect(
                    x,
                    frame.bottom-72,
                    bw,
                    52
                )
            )
        ]

        for e in events:
            if (
                e.type==pygame.KEYDOWN
                and e.key==pygame.K_ESCAPE
            ):
                self.state='menu'

            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
            ):
                for label,r in buttons:
                    if r.collidepoint(e.pos):
                        self.play_sfx(
                            'click',
                            0.7
                        )

                        if label=='BACK':
                            self.state='menu'
                        else:
                            self.game_mode=label
                            self.reset_game()
                            self.state='playing'

                        return


    def draw_mode_select(self):
        self.draw_bg(
            True,
            40
        )

        pw=min(
            780,
            self.w-90
        )

        ph=min(
            650,
            self.h-90
        )

        frame=pygame.Rect(
            (self.w-pw)//2,
            max(
                35,
                (self.h-ph)//2
            ),
            pw,
            ph
        )

        self.panel(frame)

        self.text(
            'MISSION SELECT',
            frame.y+32,
            42,
            CYAN
        )

        self.text(
            'CHOOSE YOUR MISSION PROFILE',
            frame.y+90,
            15,
            YELLOW
        )

        pygame.draw.rect(
            self.screen,
            (22,78,130),
            (
                frame.x+55,
                frame.y+122,
                frame.w-110,
                2
            )
        )

        bw=min(
            500,
            frame.w-130
        )

        bh=60

        x=frame.centerx-bw//2

        labels=[
            (
                'CLASSIC',
                'gold',
                'play'
            ),
            (
                'SURVIVAL',
                'blue',
                'right'
            ),
            (
                'BOSS RUSH',
                'orange',
                'right'
            )
        ]

        for i,(label,c,icon) in enumerate(labels):
            self.draw_pixel_button(
                self.pixel_button(
                    (
                        x,
                        frame.y+165+i*74,
                        bw,
                        bh
                    ),
                    label,
                    c,
                    icon,
                    19
                )
            )

        self.draw_pixel_button(
            self.pixel_button(
                (
                    x,
                    frame.bottom-72,
                    bw,
                    52
                ),
                'BACK',
                'red',
                'left',
                17
            )
        )


    # =========================================================
    # SHIP SELECTION
    # =========================================================

    def ship_layout(self):
        panel_w=min(
            1180,
            max(
                760,
                self.w-100
            )
        )

        panel_h=min(
            700,
            max(
                620,
                self.h-80
            )
        )

        panel_x=(self.w-panel_w)//2
        panel_y=max(
            30,
            (self.h-panel_h)//2
        )

        gap=48
        side_margin=55

        card_w=(
            panel_w-
            side_margin*2-
            gap
        )//2

        card_h=min(
            420,
            panel_h-235
        )

        card_y=panel_y+145

        cards=[
            pygame.Rect(
                panel_x+side_margin,
                card_y,
                card_w,
                card_h
            ),
            pygame.Rect(
                panel_x+
                side_margin+
                card_w+
                gap,
                card_y,
                card_w,
                card_h
            )
        ]

        back_w=250
        back_h=54

        back=pygame.Rect(
            panel_x+
            (panel_w-back_w)//2,
            panel_y+
            panel_h-72,
            back_w,
            back_h
        )

        return (
            pygame.Rect(
                panel_x,
                panel_y,
                panel_w,
                panel_h
            ),
            cards,
            back
        )


    def select_ship(self,ship_index):
        if not Player.SHIPS:
            return

        ship_index=max(
            0,
            min(
                int(ship_index),
                len(Player.SHIPS)-1
            )
        )

        self.selected_ship=ship_index

        old_score=getattr(
            self,
            'score',
            0
        )

        self.player=Player(
            self.w,
            self.h,
            self.selected_ship
        )

        self.max_hp=self.player.max_hp
        self.hp=self.max_hp
        self.score=old_score

        if self.db_ready and self.player_id:
            try:
                self.db.set_player_preference(
                    self.player_id,
                    'selected_ship',
                    self.selected_ship
                )
            except Exception:
                pass

        self.play_sfx(
            'click',
            0.75
        )

        self.show_fx(
            f'{self.player.ship_name} SELECTED',
            self.player.bullet_color,
            45
        )

        self.spawn_particles(
            self.w//2,
            self.h//2+60,
            16,
            self.player.bullet_color,
            3.0,
            3,
            28
        )


    def ship_event(self,events):
        panel,cards,back=self.ship_layout()

        for e in events:
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE:
                    self.state='menu'
                    return

                if (
                    e.key==pygame.K_1
                    and len(Player.SHIPS)>=1
                ):
                    self.select_ship(0)
                    return

                if (
                    e.key==pygame.K_2
                    and len(Player.SHIPS)>=2
                ):
                    self.select_ship(1)
                    return

            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
            ):
                for index,card in enumerate(
                    cards[:len(Player.SHIPS)]
                ):
                    if card.collidepoint(e.pos):
                        self.select_ship(index)
                        return

                if back.collidepoint(e.pos):
                    self.play_sfx(
                        'click',
                        0.7
                    )

                    self.state='menu'
                    return


    def draw_ship(self):
        self.draw_bg(
            True,
            45
        )

        panel,cards,back=self.ship_layout()

        self.panel(panel)

        self.text(
            'SHIP SELECTION',
            panel.y+30,
            46,
            CYAN
        )

        self.text(
            'CHOOSE YOUR SHIP  •  WEAPON  •  ULTIMATE',
            panel.y+88,
            18,
            YELLOW
        )

        pygame.draw.rect(
            self.screen,
            (26,70,125),
            (
                panel.x+50,
                panel.y+118,
                panel.w-100,
                2
            )
        )

        pygame.draw.rect(
            self.screen,
            CYAN,
            (
                panel.x+50,
                panel.y+118,
                155,
                2
            )
        )

        mouse=pygame.mouse.get_pos()

        for i,spec in enumerate(Player.SHIPS):
            if i>=len(cards):
                break

            r=cards[i]

            selected=self.selected_ship==i
            hovered=r.collidepoint(mouse)

            pygame.draw.rect(
                self.screen,
                (4,12,31),
                r
            )

            if selected:
                border=GREEN
                width=5

            elif hovered:
                border=CYAN
                width=4

            else:
                border=PURPLE if i==1 else BLUE
                width=3

            pygame.draw.rect(
                self.screen,
                border,
                r,
                width
            )

            pygame.draw.rect(
                self.screen,
                (20,55,100),
                r.inflate(
                    -12,
                    -12
                ),
                1
            )

            if hovered and self.animations:
                pulse=45+int(
                    35*
                    (
                        0.5+
                        0.5*
                        math.sin(
                            self.anim_time*5.0
                        )
                    )
                )

                glow=pygame.Surface(
                    (
                        r.w+20,
                        r.h+20
                    ),
                    pygame.SRCALPHA
                )

                pygame.draw.rect(
                    glow,
                    (*border,pulse),
                    glow.get_rect(),
                    4
                )

                self.screen.blit(
                    glow,
                    (
                        r.x-10,
                        r.y-10
                    )
                )

            image_path=(
                ROOT/
                'assets'/
                'images'/
                spec['image']
            )

            try:
                img=pygame.image.load(
                    str(image_path)
                ).convert_alpha()

                max_w=min(
                    205,
                    r.w-70
                )

                max_h=185

                iw,ih=img.get_size()

                scale=min(
                    max_w/max(1,iw),
                    max_h/max(1,ih)
                )

                img=pygame.transform.smoothscale(
                    img,
                    (
                        max(
                            1,
                            int(iw*scale)
                        ),
                        max(
                            1,
                            int(ih*scale)
                        )
                    )
                )

                float_y=0

                if self.animations:
                    float_y=int(
                        math.sin(
                            self.anim_time*2.2+i
                        )*5
                    )

                image_rect=img.get_rect(
                    center=(
                        r.centerx,
                        r.y+100+float_y
                    )
                )

                if self.animations:
                    glow=pygame.Surface(
                        (
                            img.get_width()+50,
                            70
                        ),
                        pygame.SRCALPHA
                    )

                    pygame.draw.ellipse(
                        glow,
                        (*spec['color'],35),
                        glow.get_rect()
                    )

                    self.screen.blit(
                        glow,
                        glow.get_rect(
                            center=(
                                image_rect.centerx,
                                image_rect.bottom-5
                            )
                        )
                    )

                self.screen.blit(
                    img,
                    image_rect
                )

            except Exception:
                pygame.draw.polygon(
                    self.screen,
                    spec['color'],
                    [
                        (
                            r.centerx,
                            r.y+35
                        ),
                        (
                            r.centerx-65,
                            r.y+155
                        ),
                        (
                            r.centerx+65,
                            r.y+155
                        )
                    ]
                )

            name_font=pygame.font.SysFont(
                'dejavusansmono',
                24,
                bold=True
            )

            name=name_font.render(
                spec['name'],
                True,
                GREEN if selected else WHITE
            )

            self.screen.blit(
                name,
                name.get_rect(
                    center=(
                        r.centerx,
                        r.y+205
                    )
                )
            )

            self.text(
                f"WEAPON: {spec['bullet'].upper()}",
                r.y+238,
                16,
                spec['color'],
                False,
                r.x+20
            )

            self.text(
                f"ULTIMATE: {spec['ultimate']}",
                r.y+266,
                16,
                YELLOW,
                False,
                r.x+20
            )

            self.text(
                f"HP {spec['hp']}    SPEED {spec['speed']:.1f}",
                r.y+294,
                15,
                WHITE,
                False,
                r.x+20
            )

            select_rect=pygame.Rect(
                r.x+18,
                r.bottom-58,
                r.w-36,
                42
            )

            label=(
                'SELECTED'
                if selected
                else 'SELECT SHIP'
            )

            color=(
                'green'
                if selected
                else (
                    'orange'
                    if hovered
                    else 'blue'
                )
            )

            self.draw_pixel_button(
                self.pixel_button(
                    select_rect,
                    label,
                    color,
                    'right',
                    16
                )
            )

        self.draw_pixel_button(
            self.pixel_button(
                back,
                'BACK',
                'red',
                'left',
                17
            )
        )

        self.text(
            '',
            panel.bottom-40,
            13,
            (180,205,225)
        )

        if self.fx_message_timer>0:
            alpha=min(
                255,
                int(
                    255*
                    self.fx_message_timer/
                    45
                )
            )

            font=pygame.font.SysFont(
                'dejavusansmono',
                22,
                bold=True
            )

            surf=font.render(
                self.fx_message,
                True,
                self.player.bullet_color
            )

            surf.set_alpha(alpha)

            self.screen.blit(
                surf,
                surf.get_rect(
                    center=(
                        self.w//2,
                        panel.bottom-100
                    )
                )
            )


    # =========================================================
    # OPTIONS
    # =========================================================

    def draw_settings(self):
        self.draw_bg(
            True,
            55
        )

        fw=min(
            820,
            self.w-90
        )

        fh=min(
            720,
            self.h-70
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                30,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'OPTIONS',
            frame.y+30,
            44,
            GOLD_LIGHT
        )

        self.text(
            'GAMEPLAY  •  AUDIO  •  DISPLAY',
            frame.y+88,
            15,
            CYAN
        )

        self.text(
            'Configure controls, music, effects, and animation.',
            frame.y+116,
            13,
            (165,200,225)
        )

        items=[
            (
                'MOBILE CONTROLS',
                'ON' if self.show_mobile else 'OFF',
                'orange',
                'menu'
            ),
            (
                'MUSIC',
                'ON' if self.music_enabled else 'OFF',
                'gold',
                'play'
            ),
            (
                'SFX',
                'ON' if self.sfx_enabled else 'OFF',
                'gold',
                'gear'
            ),
            (
                'ANIMATIONS',
                'ON' if self.animations else 'OFF',
                'orange',
                'right'
            )
        ]

        bx=frame.x+70
        bw=frame.w-140
        y=frame.y+165

        for i,(title,state,c,icon) in enumerate(items):
            row=pygame.Rect(
                bx,
                y+i*78,
                bw,
                62
            )

            accent=(
                GREEN
                if state=='ON'
                else RED
            )

            self.neon_box(
                row,
                accent,
                (4,15,36),
                9,
                False
            )

            self.text(
                title,
                row.y+17,
                15,
                WHITE,
                False,
                row.x+18
            )

            self.draw_pixel_button(
                self.pixel_button(
                    (
                        row.right-165,
                        row.y+8,
                        145,
                        46
                    ),
                    state,
                    c,
                    icon,
                    14
                )
            )

        back=pygame.Rect(
            frame.centerx-150,
            frame.bottom-66,
            300,
            50
        )

        self.draw_pixel_button(
            self.pixel_button(
                back,
                'BACK',
                'red',
                'left',
                16
            )
        )

        self.text(
            '',
            frame.bottom-30,
            11,
            (135,175,205)
        )


    # =========================================================
    # HELP
    # =========================================================

    def draw_help(self,events):
        if any(
            e.type==pygame.KEYDOWN
            and e.key in (
                pygame.K_ESCAPE,
                pygame.K_BACKSPACE
            )
            for e in events
        ):
            self.state='menu'
            return

        self.draw_bg(
            True,
            65
        )

        fw=min(
            900,
            self.w-90
        )

        fh=min(
            700,
            self.h-70
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                30,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'HELP',
            frame.y+30,
            44,
            GOLD_LIGHT
        )

        self.text(
            'CONTROLS & FEATURES',
            frame.y+86,
            15,
            CYAN
        )

        lines=[
            ('A / LEFT','MOVE LEFT'),
            ('D / RIGHT','MOVE RIGHT'),
            ('SPACE / FIRE','RAPID FIRE'),
            ('E / RIGHT SHIFT','ULTIMATE'),
            ('ESC','PAUSE / RESUME'),
            ('F11','FULLSCREEN'),
            ('MOUSE','USE PIXEL BUTTONS'),
            ('OPTIONS','SHOW / HIDE MOBILE CONTROLS'),
            ('LOGIN','MYSQL ACCOUNT AUTHENTICATION'),
            ('LEADERBOARD','SAVED SCORES FROM MYSQL')
        ]

        colw=(frame.w-130)//2

        for i,(key,desc) in enumerate(lines):
            col=i%2
            row=i//2

            r=pygame.Rect(
                frame.x+45+col*(colw+25),
                frame.y+140+row*74,
                colw,
                60
            )

            self.neon_box(
                r,
                CYAN if col==0 else BLUE,
                (4,14,34),
                8,
                False
            )

            self.text(
                key,
                r.y+9,
                12,
                YELLOW,
                False,
                r.x+15
            )

            self.text(
                desc,
                r.y+31,
                12,
                WHITE,
                False,
                r.x+15
            )

        self.text(
            '',
            frame.bottom-28,
            11,
            (150,190,220)
        )


    # =========================================================
    # LEADERBOARD
    # =========================================================

    def draw_leaderboard(self,events):
        if any(
            e.type==pygame.KEYDOWN
            and e.key==pygame.K_ESCAPE
            for e in events
        ):
            self.state='menu'
            return

        self.draw_bg(
            True,
            65
        )

        fw=min(
            980,
            self.w-80
        )

        fh=min(
            730,
            self.h-60
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                25,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'LEADERBOARD',
            frame.y+30,
            42,
            GOLD_LIGHT
        )

        self.text(
            'TOP PILOTS  //  DATABASE RANKING',
            frame.y+86,
            14,
            CYAN
        )

        head=pygame.Rect(
            frame.x+40,
            frame.y+125,
            frame.w-80,
            44
        )

        self.neon_box(
            head,
            CYAN,
            (5,20,42),
            7,
            False
        )

        self.text(
            'RANK',
            head.y+13,
            11,
            CYAN,
            False,
            head.x+15
        )

        self.text(
            'PLAYER',
            head.y+13,
            11,
            CYAN,
            False,
            head.x+95
        )

        self.text(
            'HIGH SCORE',
            head.y+13,
            11,
            CYAN,
            False,
            head.right-210
        )

        self.text(
            'GAMES',
            head.y+13,
            11,
            CYAN,
            False,
            head.right-75
        )

        rows=(
            self.db.get_leaderboard(10)
            if self.db_ready
            else []
        )

        y=head.bottom+10

        for i,rw in enumerate(rows,1):
            rr=pygame.Rect(
                frame.x+40,
                y,
                frame.w-80,
                48
            )

            mine=(
                rw['username']==self.username
            )

            self.neon_box(
                rr,
                GREEN if mine else (38,105,170),
                (3,13,31),
                6,
                False
            )

            self.text(
                f'{i:02d}',
                rr.y+13,
                13,
                GOLD_LIGHT if i<=3 else WHITE,
                False,
                rr.x+18
            )

            self.text(
                str(rw['username'])[:22],
                rr.y+13,
                13,
                GREEN if mine else WHITE,
                False,
                rr.x+95
            )

            self.text(
                f'{rw["high_score"]:>8}',
                rr.y+13,
                13,
                GOLD_LIGHT,
                False,
                rr.right-210
            )

            self.text(
                f'{rw["games_played"]}',
                rr.y+13,
                13,
                WHITE,
                False,
                rr.right-75
            )

            y+=55

            if y>frame.bottom-95:
                break

        back=pygame.Rect(
            frame.centerx-140,
            frame.bottom-62,
            280,
            48
        )

        self.draw_pixel_button(
            self.pixel_button(
                back,
                'BACK',
                'red',
                'left',
                15
            )
        )

        for e in events:
            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
                and back.collidepoint(e.pos)
            ):
                self.play_sfx(
                    'click',
                    0.7
                )

                self.state='menu'


    # =========================================================
    # PROFILE
    # =========================================================

    def draw_profile(self,events):
        if any(
            e.type==pygame.KEYDOWN
            and e.key==pygame.K_ESCAPE
            for e in events
        ):
            self.state='menu'
            return

        self.draw_bg(
            True,
            65
        )

        fw=min(
            760,
            self.w-90
        )

        fh=min(
            640,
            self.h-80
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                35,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'PLAYER PROFILE',
            frame.y+30,
            40,
            GOLD_LIGHT
        )

        self.text(
            'PILOT INFORMATION  //  ACCOUNT STATUS',
            frame.y+84,
            14,
            CYAN
        )

        row=(
            self.db.get_player(
                player_id=self.player_id
            )
            if self.db_ready
            else None
        )

        vals=[
            (
                'USERNAME',
                self.username
            ),
            (
                'HIGH SCORE',
                str(
                    row['high_score']
                    if row
                    else 0
                )
            ),
            (
                'GAMES PLAYED',
                str(
                    row['games_played']
                    if row
                    else 0
                )
            ),
            (
                'DATABASE',
                'CONNECTED'
                if self.db_ready
                else 'OFFLINE'
            )
        ]

        y=frame.y+140

        for i,(label,val) in enumerate(vals):
            rr=pygame.Rect(
                frame.x+55,
                y+i*78,
                frame.w-110,
                60
            )

            accent=(
                GREEN
                if label=='DATABASE'
                and val=='CONNECTED'
                else CYAN
            )

            self.neon_box(
                rr,
                accent,
                (4,15,35),
                8,
                False
            )

            self.text(
                label,
                rr.y+10,
                11,
                accent,
                False,
                rr.x+16
            )

            self.text(
                val,
                rr.y+29,
                17,
                WHITE,
                False,
                rr.x+16
            )

        back=pygame.Rect(
            frame.centerx-140,
            frame.bottom-64,
            280,
            48
        )

        self.draw_pixel_button(
            self.pixel_button(
                back,
                'BACK',
                'red',
                'left',
                15
            )
        )

        for e in events:
            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
                and back.collidepoint(e.pos)
            ):
                self.play_sfx(
                    'click',
                    0.7
                )

                self.state='menu'


    # =========================================================
    # GAMEPLAY
    # =========================================================

    def update_play(self,events):
        if any(
            e.type==pygame.KEYDOWN
            and e.key==pygame.K_ESCAPE
            for e in events
        ):
            self.space_fire_latched=False
            self.state='paused'
            return

        keys=pygame.key.get_pressed()

        if (
            keys[pygame.K_LEFT]
            or keys[pygame.K_a]
        ):
            self.player.move_left()

        if (
            keys[pygame.K_RIGHT]
            or keys[pygame.K_d]
        ):
            self.player.move_right()

        # -----------------------------------------------------
        # SPACE = RELIABLE HOLD-TO-FIRE / RAPID FIRE
        # -----------------------------------------------------

        for e in events:
            if (
                e.type==pygame.KEYDOWN
                and e.key==pygame.K_SPACE
            ):
                self.space_fire_latched=True

            elif (
                e.type==pygame.KEYUP
                and e.key==pygame.K_SPACE
            ):
                self.space_fire_latched=False

        space_held=(
            bool(keys[pygame.K_SPACE])
            or self.space_fire_latched
        )

        mobile_fire=self.buttons.handle_mouse(
            self.player,
            events
        )

        fire_held=space_held or mobile_fire

        if self.fire_cooldown>0:
            self.fire_cooldown-=1

        if (
            fire_held
            and self.fire_cooldown<=0
        ):
            points=self.player.get_fire_points()
            variant=self.player.bullet_type

            for idx,(fx,fy) in enumerate(points):
                vx=0

                if (
                    variant=='blue'
                    and len(points)==3
                ):
                    vx=(
                        -1.15,
                        0,
                        1.15
                    )[idx]

                self.bullets.append(
                    Bullet(
                        fx,
                        fy,
                        variant,
                        vx,
                        damage=1
                    )
                )

            self.fire_cooldown=5

            if self.space_fire_sound_timer<=0:
                self.play_sfx(
                    'shoot',
                    0.34
                )

                self.space_fire_sound_timer=3

            self.spawn_particles(
                self.player.x+
                self.player.width/2,
                self.player.y+
                self.player.height-6,
                4,
                self.player.bullet_color,
                1.8,
                2,
                14
            )

        if self.space_fire_sound_timer>0:
            self.space_fire_sound_timer-=1

        # -----------------------------------------------------
        # PLAYER ULTIMATE
        # -----------------------------------------------------

        if self.ultimate_cooldown>0:
            self.ultimate_cooldown-=1

        if (
            any(
                e.type==pygame.KEYDOWN
                and e.key in (
                    pygame.K_e,
                    pygame.K_RSHIFT
                )
                for e in events
            )
            and self.ultimate_charge>=100
            and self.ultimate_cooldown<=0
        ):
            self.activate_player_ultimate()

        self.player.keep_inside_screen()

        for b in self.bullets:
            b.update()

        self.bullets=[
            b
            for b in self.bullets
            if b.is_active
        ]

        self.timer+=1

        drop_interval=max(
            55,
            125-self.stage*5
        )

        if self.timer>=drop_interval:
            waiting=[
                e
                for e in self.enemies
                if e.state=='waiting'
            ]

            drops=min(
                1+self.stage//4,
                len(waiting),
                3
            )

            for e in (
                random.sample(
                    waiting,
                    drops
                )
                if drops
                else []
            ):
                tx,ty=(
                    self.player_history[0]
                    if self.player_history
                    else (
                        self.player.x,
                        self.player.y
                    )
                )

                e.start_drop(
                    tx,
                    ty
                )

            self.timer=0

        all_off=True

        for e in self.enemies:
            e.update()

            all_off=(
                all_off
                and e.state=='offscreen'
            )

            if e.update_fire_timer():
                ex,ey=e.get_fire_position()

                tx=(
                    self.player.x+
                    self.player.width/2
                )

                ty=(
                    self.player.y+
                    self.player.height/2
                )

                dx=tx-ex
                dy=ty-ey

                dist=max(
                    1.0,
                    (dx*dx+dy*dy)**0.5
                )

                speed=(
                    5.8+
                    min(
                        3.4,
                        self.stage*0.22
                    )
                )

                self.enemy_bullets.append(
                    EnemyBullet(
                        ex,
                        ey,
                        dx/dist*speed,
                        dy/dist*speed,
                        damage=1,
                        size=9,
                        color=(255,65,85)
                    )
                )

                if self.enemy_fire_sound_timer<=0:
                    self.play_sfx(
                        'enemy_bullet',
                        0.42
                    )

                    self.enemy_fire_sound_timer=8

        if (
            self.boss
            and self.boss.state!='defeated'
        ):
            self.boss.update()

            if self.boss.update_fire_timer():
                for i,(bx,by) in enumerate(
                    self.boss.get_fire_positions()
                ):
                    tx=(
                        self.player.x+
                        self.player.width/2
                    )

                    ty=(
                        self.player.y+
                        self.player.height/2
                    )

                    dx=tx-bx
                    dy=ty-by

                    dist=max(
                        1.0,
                        (dx*dx+dy*dy)**0.5
                    )

                    speed=(
                        6.4+
                        min(
                            3.8,
                            self.stage*0.24
                        )
                    )

                    if i==1:
                        dx-=45
                    elif i==2:
                        dx+=45

                    dist=max(
                        1.0,
                        (dx*dx+dy*dy)**0.5
                    )

                    self.enemy_bullets.append(
                        EnemyBullet(
                            bx,
                            by,
                            dx/dist*speed,
                            dy/dist*speed,
                            damage=1,
                            size=11,
                            color=(190,80,255)
                        )
                    )

                if self.enemy_fire_sound_timer<=0:
                    self.play_sfx(
                        'enemy_bullet',
                        0.55
                    )

                    self.enemy_fire_sound_timer=8

            if self.boss.update_ultimate_timer():
                self.play_sfx(
                    'warning',
                    0.95
                )

                self.fx_flash=6

                self.show_fx(
                    f'{self.boss.name} ULTIMATE',
                    self.boss.color,
                    48
                )

                self.spawn_particles(
                    self.boss.x+
                    self.boss.width/2,
                    self.boss.y+
                    self.boss.height/2,
                    32,
                    self.boss.color,
                    5.5,
                    5,
                    38
                )

                pattern,shots=(
                    self.boss.get_ultimate_pattern()
                )

                for bx,by,vx,vy in shots:
                    self.enemy_bullets.append(
                        EnemyBullet(
                            bx,
                            by,
                            vx,
                            vy,
                            damage=1,
                            size=(
                                14
                                if pattern!='spiral'
                                else 12
                            ),
                            color=self.boss.color
                        )
                    )

                if self.stage>=5:
                    for vx in (
                        -4.8,
                        -3.2,
                        -1.6,
                        0,
                        1.6,
                        3.2,
                        4.8
                    ):
                        self.enemy_bullets.append(
                            EnemyBullet(
                                self.boss.x+
                                self.boss.width/2,
                                self.boss.y+
                                self.boss.height*0.76,
                                vx,
                                7.6,
                                damage=1,
                                size=11,
                                color=(255,80,110)
                            )
                        )

        for eb in self.enemy_bullets:
            eb.update(
                self.w,
                self.h
            )

        self.enemy_bullets=[
            eb
            for eb in self.enemy_bullets
            if eb.is_active
        ]

        if self.enemy_fire_sound_timer>0:
            self.enemy_fire_sound_timer-=1

        if (
            self.boss
            and self.boss.state=='defeated'
            and not self.boss_defeated
        ):
            self.boss_defeated=True
            self.score+=self.boss.points
            self.stage+=1

            self.spawn_number=min(
                20,
                6+self.stage
            )

            self.ultimate_charge=min(
                100,
                self.ultimate_charge+30
            )

            self.spawn_enemies()

        elif not self.boss and all_off:
            self.stage+=1

            self.spawn_number=min(
                20,
                6+self.stage
            )

            self.ultimate_charge=min(
                100,
                self.ultimate_charge+20
            )

            self.spawn_enemies()

        self.player_history.append(
            (
                self.player.x,
                self.player.y
            )
        )

        self.player_history=self.player_history[-60:]

        self.check_collisions()
        self.draw_game()


    def activate_player_ultimate(self):
        self.ultimate_charge=0
        self.ultimate_cooldown=90

        self.play_sfx(
            'ultimate',
            0.9
        )

        self.fx_flash=8

        self.show_fx(
            self.player.ultimate_name,
            self.player.bullet_color,
            60
        )

        self.spawn_particles(
            self.player.x+
            self.player.width/2,
            self.player.y+15,
            34,
            self.player.bullet_color,
            5.0,
            5,
            42
        )

        cx=(
            self.player.x+
            self.player.width/2
        )

        y=self.player.y+8

        if self.player.selected_ship==0:
            for vx in (
                -0.9,
                -0.45,
                0,
                0.45,
                0.9
            ):
                self.bullets.append(
                    Bullet(
                        cx,
                        y,
                        'pink',
                        vx,
                        damage=3,
                        scale=1.35
                    )
                )

        else:
            for vx in (
                -2.5,
                -1.7,
                -0.85,
                0,
                0.85,
                1.7,
                2.5
            ):
                self.bullets.append(
                    Bullet(
                        cx,
                        y,
                        'blue',
                        vx,
                        damage=3,
                        scale=1.25
                    )
                )


    def draw_game(self):
        self.draw_bg()

        self.player.draw(
            self.screen
        )

        for e in self.enemies:
            e.draw(
                self.screen
            )

        if self.boss:
            self.boss.draw(
                self.screen
            )

        for b in self.bullets:
            b.draw(
                self.screen
            )

        for eb in self.enemy_bullets:
            eb.draw(
                self.screen
            )

        self.draw_particles()

        hud_h=min(
            176,
            max(
                150,
                int(self.h*0.17)
            )
        )

        top=12
        margin=18
        gap=10

        left_w=min(
            390,
            max(
                300,
                int(self.w*0.23)
            )
        )

        right_w=min(
            330,
            max(
                280,
                int(self.w*0.20)
            )
        )

        center_w=(
            self.w-
            (
                margin*2+
                left_w+
                right_w+
                gap*2
            )
        )

        left=pygame.Rect(
            margin,
            top,
            left_w,
            hud_h-24
        )

        self.neon_box(
            left,
            CYAN,
            (3,12,31),
            16,
            True
        )

        self.text(
            'SPACE INVADERS',
            left.y+12,
            18,
            CYAN,
            False,
            left.x+18
        )

        self.text(
            f'SCORE  {self.score:06d}',
            left.y+42,
            21,
            WHITE,
            False,
            left.x+18
        )

        stage_box=pygame.Rect(
            left.x+18,
            left.y+82,
            (left.w-48)//2,
            58
        )

        hp_box=pygame.Rect(
            stage_box.right+10,
            stage_box.y,
            stage_box.w,
            58
        )

        self.hud_box(
            stage_box,
            'STAGE',
            str(self.stage),
            GOLD_LIGHT,
            GOLD_LIGHT,
            10,
            20
        )

        hp_color=(
            GREEN
            if self.hp>self.max_hp*0.4
            else RED
        )

        self.neon_box(
            hp_box,
            hp_color,
            (4,15,34),
            8,
            False
        )

        self.text(
            'HP',
            hp_box.y+9,
            10,
            hp_color,
            False,
            hp_box.x+12
        )

        self.text(
            f'{self.hp}/{self.max_hp}',
            hp_box.y+28,
            19,
            WHITE,
            False,
            hp_box.x+12
        )

        self.progress_bar(
            (
                hp_box.x+86,
                hp_box.y+25,
                hp_box.w-98,
                14
            ),
            self.hp,
            self.max_hp,
            hp_color
        )

        center=pygame.Rect(
            left.right+gap,
            top,
            center_w,
            hud_h-24
        )

        self.neon_box(
            center,
            self.player.bullet_color,
            (3,13,34),
            16,
            True
        )

        self.text(
            (
                f'{self.player.ship_name.upper()}'
                f'  //  '
                f'{self.player.bullet_type.upper()} WEAPON'
            ),
            center.y+13,
            17,
            self.player.bullet_color,
            False,
            center.x+22
        )

        self.text(
            'HOLD SPACE  //  RAPID FIRE',
            center.y+45,
            13,
            WHITE,
            False,
            center.x+22
        )

        self.text(
            f'ULTIMATE [E]   {int(self.ultimate_charge):03d}%',
            center.y+76,
            12,
            (
                GOLD_LIGHT
                if self.ultimate_charge<100
                else GREEN
            ),
            False,
            center.x+22
        )

        self.progress_bar(
            (
                center.x+22,
                center.y+105,
                center.w-44,
                18
            ),
            self.ultimate_charge,
            100,
            (
                GREEN
                if self.ultimate_charge>=100
                else self.player.bullet_color
            )
        )

        right=pygame.Rect(
            center.right+gap,
            top,
            right_w,
            hud_h-24
        )

        difficulty=(
            'ELITE'
            if self.stage>=8
            else (
                'HARD'
                if self.stage>=4
                else 'NORMAL'
            )
        )

        dcol=(
            RED
            if difficulty=='ELITE'
            else (
                ORANGE
                if difficulty=='HARD'
                else CYAN
            )
        )

        self.neon_box(
            right,
            dcol,
            (3,13,32),
            16,
            True
        )

        self.text(
            difficulty,
            right.y+16,
            18,
            dcol
        )

        self.text(
            f'ENEMY PRESSURE +{self.stage*4}%',
            right.y+48,
            12,
            WHITE
        )

        self.text(
            'ESC  //  PAUSE',
            right.y+78,
            13,
            (165,205,230)
        )

        pygame.draw.rect(
            self.screen,
            (28,78,125),
            (
                right.x+18,
                right.y+108,
                right.w-36,
                2
            )
        )

        self.text(
            self.game_mode,
            right.y+117,
            11,
            GOLD_LIGHT
        )

        if (
            self.boss
            and self.boss.state!='defeated'
        ):
            br=pygame.Rect(
                self.w//2-250,
                hud_h+8,
                500,
                50
            )

            self.neon_box(
                br,
                RED,
                (30,7,18),
                10,
                True
            )

            self.text(
                f'BOSS  //  {self.boss.name.upper()}',
                br.y+15,
                14,
                RED
            )

            boss_hp=getattr(
                self.boss,
                'hp',
                0
            )

            boss_max=max(
                1,
                getattr(
                    self.boss,
                    'max_hp',
                    boss_hp or 1
                )
            )

            self.progress_bar(
                (
                    br.x+210,
                    br.y+17,
                    br.w-225,
                    14
                ),
                boss_hp,
                boss_max,
                RED
            )

        self.buttons.draw(
            self.screen,
            self.small
        )

        if self.fx_message_timer>0:
            alpha=min(
                255,
                int(
                    255*
                    self.fx_message_timer/
                    35
                )
            )

            f=pygame.font.SysFont(
                'dejavusansmono',
                30,
                bold=True
            )

            surf=f.render(
                self.fx_message,
                True,
                self.player.bullet_color
            )

            surf.set_alpha(alpha)

            self.screen.blit(
                surf,
                surf.get_rect(
                    center=(
                        self.w//2,
                        min(
                            self.h-220,
                            hud_h+220
                        )
                    )
                )
            )

        if self.fx_flash>0:
            ov=pygame.Surface(
                (self.w,self.h),
                pygame.SRCALPHA
            )

            ov.fill(
                (
                    255,
                    255,
                    255,
                    min(
                        70,
                        self.fx_flash*7
                    )
                )
            )

            self.screen.blit(
                ov,
                (0,0)
            )


    # =========================================================
    # PAUSE
    # =========================================================

    def draw_pause(self,events):
        if any(
            e.type==pygame.KEYDOWN
            and e.key==pygame.K_ESCAPE
            for e in events
        ):
            self.state='playing'
            return

        self.draw_game()

        ov=pygame.Surface(
            (self.w,self.h),
            pygame.SRCALPHA
        )

        ov.fill(
            (0,4,18,190)
        )

        self.screen.blit(
            ov,
            (0,0)
        )

        fw=min(
            700,
            self.w-90
        )

        fh=min(
            560,
            self.h-100
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            max(
                50,
                (self.h-fh)//2
            ),
            fw,
            fh
        )

        self.panel(frame)

        self.text(
            'PAUSED',
            frame.y+30,
            46,
            GOLD_LIGHT
        )

        self.text(
            'MISSION SUSPENDED  //  SELECT AN ACTION',
            frame.y+88,
            13,
            CYAN
        )

        labels=[
            (
                'CONTINUE',
                'green',
                'right'
            ),
            (
                'NEW GAME',
                'green',
                'plus'
            ),
            (
                'SAVE',
                'blue',
                'save'
            ),
            (
                'MAIN MENU',
                'orange',
                'menu'
            ),
            (
                'EXIT',
                'red',
                'x'
            )
        ]

        bw=min(
            430,
            frame.w-120
        )

        bh=54

        x=frame.centerx-bw//2
        rects=[]

        for i,(label,c,icon) in enumerate(labels):
            r=pygame.Rect(
                x,
                frame.y+130+i*62,
                bw,
                bh
            )

            rects.append(r)

            self.draw_pixel_button(
                self.pixel_button(
                    r,
                    label,
                    c,
                    icon,
                    16
                )
            )

        for e in events:
            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
            ):
                if rects[0].collidepoint(e.pos):
                    self.state='playing'

                elif rects[1].collidepoint(e.pos):
                    self.reset_game()

                elif rects[2].collidepoint(e.pos):
                    self.save_current_game()

                elif rects[3].collidepoint(e.pos):
                    self.state='menu'

                elif rects[4].collidepoint(e.pos):
                    pygame.event.post(
                        pygame.event.Event(
                            pygame.QUIT
                        )
                    )


    def update_blink(self):
        self.player.update_blink()
        self.state_timer+=1

        if self.state_timer>=120:
            self.end_game()


    # =========================================================
    # GAME OVER
    # =========================================================

    def draw_game_over(self,events):
        if not self.score_saved:
            self.play_sfx(
                'gameover',
                0.85
            )

            if (
                self.db_ready
                and self.player_id
            ):
                self.db.save_score(
                    self.player_id,
                    self.score
                )

            self.leaderboard=(
                self.db.get_leaderboard(5)
                if self.db_ready
                else []
            )

            self.score_saved=True

        self.draw_bg(
            True,
            0
        )

        fw=min(
            840,
            self.w-48
        )

        fh=min(
            520,
            self.h-40
        )

        frame=pygame.Rect(
            (self.w-fw)//2,
            (self.h-fh)//2,
            fw,
            fh
        )

        self.glass_panel(
            frame,
            150,
            30
        )

        title_font=pygame.font.SysFont(
            'dejavusansmono',
            52,
            bold=True
        )
        title_left=title_font.render(
            'GAME ',
            True,
            CYAN
        )
        title_right=title_font.render(
            'OVER',
            True,
            (220,105,255)
        )
        title_x=frame.centerx-(
            title_left.get_width()+title_right.get_width()
        )//2
        self.screen.blit(
            title_left,
            (title_x,frame.y+38)
        )
        self.screen.blit(
            title_right,
            (
                title_x+title_left.get_width(),
                frame.y+38
            )
        )

        self.text(
            'MISSION TERMINATED',
            frame.y+105,
            16,
            (175,225,255)
        )

        score_box=pygame.Rect(
            frame.x+70,
            frame.y+165,
            frame.w-140,
            108
        )

        self.glass_panel(
            score_box,
            95,
            24
        )

        self.text(
            'FINAL SCORE',
            score_box.y+16,
            16,
            (140,220,255)
        )

        self.text(
            f'{self.score:06d}',
            score_box.y+47,
            36,
            CYAN
        )

        self.text(
            f'PLAYER  //  {self.username.upper()}',
            frame.y+305,
            17,
            (140,225,255)
        )

        enter_rect=pygame.Rect(
            frame.centerx-145,
            frame.y+370,
            290,
            58
        )

        hovered=enter_rect.collidepoint(
            pygame.mouse.get_pos()
        )
        self.glass_panel(
            enter_rect,
            175 if hovered else 110,
            18
        )
        self.text(
            'ENTER',
            enter_rect.y+17,
            20,
            WHITE
        )
        pygame.draw.polygon(
            self.screen,
            CYAN,
            (
                (enter_rect.right-34,enter_rect.centery-8),
                (enter_rect.right-22,enter_rect.centery),
                (enter_rect.right-34,enter_rect.centery+8)
            )
        )

        for e in events:
            if (
                e.type==pygame.KEYDOWN
                and e.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER
                )
            ):
                self.play_sfx('click',0.7)
                self.state='menu'
                return

            if (
                e.type==pygame.MOUSEBUTTONDOWN
                and e.button==1
                and enter_rect.collidepoint(e.pos)
            ):
                self.play_sfx('click',0.7)
                self.state='menu'
                return


    def end_game(self):
        self.state='game_over'


    # =========================================================
    # COLLISIONS
    # =========================================================

    def check_collisions(self):
        pr=self.player.get_rect()

        # -----------------------------------------------------
        # ENEMY PROJECTILES
        # -----------------------------------------------------
        for eb in self.enemy_bullets:
            if (
                eb.is_active
                and pr.colliderect(
                    eb.get_rect()
                )
            ):
                eb.is_active=False

                self.hp=max(
                    0,
                    self.hp-eb.damage
                )

                self.play_sfx(
                    'hit',
                    0.55
                )

                self.fx_flash=5

                self.spawn_particles(
                    self.player.x+
                    self.player.width/2,
                    self.player.y+
                    self.player.height/2,
                    15,
                    (255,70,90),
                    4,
                    4,
                    28
                )

                if self.hp<=0:
                    self.play_sfx(
                        'gameover',
                        0.85
                    )

                    self.state='blinking'
                    self.player.is_blinking=True
                    self.state_timer=0
                    return

                self.player.x=(
                    self.w//2-
                    self.player.width//2
                )

                self.player.visible=True
                break

        # -----------------------------------------------------
        # CONTACT DAMAGE
        # -----------------------------------------------------
        for e in self.enemies:
            if e.state=='offscreen':
                continue

            if pr.colliderect(
                e.get_rect()
            ):
                e.state='offscreen'

                self.hp=max(
                    0,
                    self.hp-1
                )

                if self.hp<=0:
                    self.play_sfx(
                        'gameover',
                        0.85
                    )

                    self.state='blinking'
                    self.player.is_blinking=True
                    self.state_timer=0
                    return

                self.player.x=(
                    self.w//2-
                    self.player.width//2
                )

                self.player.visible=True
                return

        # -----------------------------------------------------
        # PLAYER BULLETS
        # -----------------------------------------------------
        for b in self.bullets:
            if not b.is_active:
                continue

            hit_something=False

            for e in self.enemies:
                if e.state=='offscreen':
                    continue

                if b.get_rect().colliderect(
                    e.get_rect()
                ):
                    if e.hit(b.damage):
                        self.score+=e.points

                        self.ultimate_charge=min(
                            100,
                            self.ultimate_charge+8
                        )

                        self.play_sfx(
                            'explosion',
                            0.48
                        )

                        self.spawn_particles(
                            e.x+e.width/2,
                            e.y+e.height/2,
                            18,
                            (255,170,50),
                            4.2,
                            4,
                            32
                        )

                    else:
                        self.score+=1

                        self.ultimate_charge=min(
                            100,
                            self.ultimate_charge+1
                        )

                        self.play_sfx(
                            'hit',
                            0.24
                        )

                        self.spawn_particles(
                            e.x+e.width/2,
                            e.y+e.height/2,
                            5,
                            (255,220,90),
                            2.5,
                            2,
                            18
                        )

                    b.is_active=False
                    hit_something=True
                    break

            if hit_something:
                continue

            if (
                self.boss
                and self.boss.state!='defeated'
                and b.get_rect().colliderect(
                    self.boss.get_rect()
                )
            ):
                if self.boss.hit(
                    b.damage
                ):
                    self.play_sfx(
                        'explosion',
                        0.9
                    )

                    self.fx_flash=10

                    self.spawn_particles(
                        self.boss.x+
                        self.boss.width/2,
                        self.boss.y+
                        self.boss.height/2,
                        45,
                        (255,80,180),
                        6,
                        6,
                        55
                    )

                else:
                    self.play_sfx(
                        'hit',
                        0.28
                    )

                    self.spawn_particles(
                        self.boss.x+
                        self.boss.width/2,
                        self.boss.y+
                        self.boss.height/2,
                        7,
                        (255,100,220),
                        3,
                        3,
                        20
                    )

                b.is_active=False

                self.ultimate_charge=min(
                    100,
                    self.ultimate_charge+1
                )

        self.bullets=[
            b
            for b in self.bullets
            if b.is_active
        ]

        self.enemy_bullets=[
            b
            for b in self.enemy_bullets
            if b.is_active
        ]