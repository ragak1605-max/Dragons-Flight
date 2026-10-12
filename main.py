import pygame
import random
import math
import io
import wave
import struct

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False

WIDTH, HEIGHT = 900, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dragon's Flight")
clock = pygame.time.Clock()

font_small = pygame.font.Font(None, 25)
font = pygame.font.Font(None, 34)
font_big = pygame.font.Font(None, 58)
font_huge = pygame.font.Font(None, 82)

WHITE = (255, 255, 255)
BLACK = (10, 8, 18)
RED = (220, 45, 55)
ORANGE = (255, 130, 30)
YELLOW = (255, 220, 70)
GOLD = (255, 190, 55)
GREEN = (60, 190, 100)
BLUE = (70, 170, 255)
PURPLE = (130, 55, 190)
PINK = (220, 60, 130)
CYAN = (80, 230, 255)

dragon_image = pygame.image.load("assets/dragon.png").convert_alpha()
gem_image = pygame.image.load("assets/gem.png").convert_alpha()
tower_top_image = pygame.image.load("assets/tower_top.png").convert_alpha()
tower_bottom_image = pygame.image.load("assets/tower_bottom.png").convert_alpha()

try:
    level1_bg = pygame.image.load("assets/level1_bg.png").convert()
    level2_bg = pygame.image.load("assets/level2_bg.png").convert()
    level3_bg = pygame.image.load("assets/level3_bg.png").convert()
    cover_bg = pygame.image.load("assets/cover_bg.png").convert()

    level1_bg = pygame.transform.smoothscale(level1_bg, (WIDTH, HEIGHT))
    level2_bg = pygame.transform.smoothscale(level2_bg, (WIDTH, HEIGHT))
    level3_bg = pygame.transform.smoothscale(level3_bg, (WIDTH, HEIGHT))
    cover_bg = pygame.transform.smoothscale(cover_bg, (WIDTH, HEIGHT))
except (pygame.error, FileNotFoundError):
    level1_bg = None
    level2_bg = None
    level3_bg = None
    cover_bg = None

dragon_image = pygame.transform.smoothscale(dragon_image, (75, 60))
gem_image = pygame.transform.smoothscale(gem_image, (32, 32))

TOWER_WIDTH = 230
TOWER_HEIGHT = 500

tower_top_image = pygame.transform.smoothscale(
    tower_top_image,
    (TOWER_WIDTH, TOWER_HEIGHT)
)

tower_top_image = tower_top_image.subsurface(
    (0, 0, TOWER_WIDTH, 470)
)

tower_bottom_image = pygame.transform.smoothscale(
    tower_bottom_image,
    (TOWER_WIDTH, TOWER_HEIGHT)
)


def create_tone(frequency, duration, volume=0.25):
    if not SOUND_ENABLED:
        return None

    rate = 44100
    samples = int(rate * duration)
    data = bytearray()

    for i in range(samples):
        t = i / rate

        fade_in = min(
            1,
            i / max(1, int(rate * 0.02))
        )

        fade_out = min(
            1,
            (samples - i) / max(1, int(rate * 0.05))
        )

        envelope = fade_in * fade_out

        value = int(
            32767
            * volume
            * envelope
            * math.sin(
                2 * math.pi * frequency * t
            )
        )

        data.extend(struct.pack("<h", value))

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(data)

    try:
        return pygame.mixer.Sound(
            buffer=buffer.getvalue()
        )
    except pygame.error:
        return None


def play_sound(sound):
    if SOUND_ENABLED and sound:
        try:
            sound.play()
        except pygame.error:
            pass


flap_sound = create_tone(520, 0.08, 0.22)
gem_sound = create_tone(900, 0.12, 0.25)
hit_sound = create_tone(150, 0.18, 0.28)
fireball_sound = create_tone(240, 0.10, 0.20)
boss_hit_sound = create_tone(750, 0.10, 0.25)
warning_sound = create_tone(300, 0.35, 0.25)
victory_sound = create_tone(1000, 0.45, 0.25)
level_sound = create_tone(650, 0.22, 0.22)

dragon_x = 180
dragon_y = 300
dragon_velocity = 0

gravity = 0.45
flap_strength = -8

score = 0
high_score = 0
hearts = 3
level = 1

menu = True
paused = False
game_over = False
victory = False

combo = 0
combo_multiplier = 1
last_gem_time = 0
combo_timeout = 2500

combo_popup = ""
combo_popup_timer = 0

level_transition = False
level_transition_timer = 0
level_transition_duration = 1800

countdown_active = False
countdown_start_time = 0
countdown_duration = 4000

screen_shake = 0
damage_flash = 0

boss_warning = False
boss_fight = False
warning_start_time = 0

boss_x = 760
boss_y = 300

boss_hp = 5
boss_max_hp = 5

boss_entering = False
boss_enter_start = 0

boss_fireballs = []
player_fireballs = []
boss_hit_effects = []

last_boss_shot = 0
boss_shot_delay = 1300

last_player_shot = 0
player_shot_delay = 350

towers = []
gems = []

spawn_timer = 0

particles = []
gem_particles = []
fire_trails = []

victory_sound_played = False


def damage_effect():
    global screen_shake, damage_flash

    screen_shake = 12
    damage_flash = 170


def particle_burst(x, y, color, amount=10):
    for _ in range(amount):
        particles.append({
            "x": x,
            "y": y,
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-3, 3),
            "life": random.randint(20, 45),
            "color": color,
            "size": random.randint(2, 5)
        })


def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.05
        p["life"] -= 1

        if p["life"] <= 0:
            particles.remove(p)


def draw_particles():
    for p in particles:
        pygame.draw.circle(
            screen,
            p["color"],
            (int(p["x"]), int(p["y"])),
            p["size"]
        )


def update_gem_particles():
    for p in gem_particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1

        if p["life"] <= 0:
            gem_particles.remove(p)


def draw_gem_particles():
    for p in gem_particles:
        pygame.draw.circle(
            screen,
            YELLOW,
            (int(p["x"]), int(p["y"])),
            3
        )


def gem_burst(x, y):
    for _ in range(14):
        gem_particles.append({
            "x": x,
            "y": y,
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-3, 3),
            "life": random.randint(20, 40)
        })


def add_fire_trail(x, y):
    fire_trails.append({
        "x": x,
        "y": y,
        "life": 18
    })


def update_fire_trails():
    for p in fire_trails[:]:
        p["life"] -= 1

        if p["life"] <= 0:
            fire_trails.remove(p)


def draw_fire_trails():
    for p in fire_trails:
        pygame.draw.circle(
            screen,
            ORANGE,
            (int(p["x"]), int(p["y"])),
            max(2, p["life"] // 3)
        )


def draw_hearts(x, y):
    for i in range(3):
        heart_x = x + i * 38

        if i < hearts:
            color = RED

            pygame.draw.circle(
                screen,
                color,
                (heart_x + 9, y + 8),
                9
            )

            pygame.draw.circle(
                screen,
                color,
                (heart_x + 23, y + 8),
                9
            )

            pygame.draw.polygon(
                screen,
                color,
                [
                    (heart_x, y + 10),
                    (heart_x + 32, y + 10),
                    (heart_x + 16, y + 30)
                ]
            )

        else:
            pygame.draw.circle(
                screen,
                (75, 25, 35),
                (heart_x + 9, y + 8),
                9,
                2
            )

            pygame.draw.circle(
                screen,
                (75, 25, 35),
                (heart_x + 23, y + 8),
                9,
                2
            )

            pygame.draw.polygon(
                screen,
                (75, 25, 35),
                [
                    (heart_x, y + 10),
                    (heart_x + 32, y + 10),
                    (heart_x + 16, y + 30)
                ],
                2
            )


def lose_heart():
    global hearts
    global combo
    global combo_multiplier
    global game_over

    if hearts <= 0:
        return

    hearts -= 1

    combo = 0
    combo_multiplier = 1

    damage_effect()

    play_sound(hit_sound)

    if hearts <= 0:
        hearts = 0
        game_over = True
        update_high_score()


def reset_game():
    global dragon_y
    global dragon_velocity
    global score
    global hearts
    global level
    global menu
    global paused
    global game_over
    global victory
    global boss_warning
    global boss_fight
    global boss_hp
    global boss_x
    global boss_y
    global boss_fireballs
    global player_fireballs
    global boss_hit_effects
    global towers
    global gems
    global spawn_timer
    global combo
    global combo_multiplier
    global last_gem_time
    global combo_popup
    global combo_popup_timer
    global level_transition
    global level_transition_timer
    global boss_entering
    global victory_sound_played
    global countdown_active
    global countdown_start_time

    dragon_y = 300
    dragon_velocity = 0

    score = 0
    hearts = 3
    level = 1

    menu = False
    paused = False
    game_over = False
    victory = False

    boss_warning = False
    boss_fight = False

    boss_hp = boss_max_hp
    boss_x = 760
    boss_y = 300

    boss_fireballs.clear()
    player_fireballs.clear()
    boss_hit_effects.clear()

    towers.clear()
    gems.clear()

    particles.clear()
    gem_particles.clear()
    fire_trails.clear()

    spawn_timer = 0

    combo = 0
    combo_multiplier = 1
    last_gem_time = 0

    combo_popup = ""
    combo_popup_timer = 0

    level_transition = True
    level_transition_timer = 0

    boss_entering = False

    victory_sound_played = False

    countdown_active = True
    countdown_start_time = pygame.time.get_ticks()


def update_high_score():
    global high_score

    if score > high_score:
        high_score = score


def update_level():
    global level
    global level_transition
    global level_transition_timer

    new_level = level

    if score < 10:
        new_level = 1
    elif score < 25:
        new_level = 2
    elif score < 30:
        new_level = 3

    if new_level != level:
        level = new_level

        level_transition = True
        level_transition_timer = pygame.time.get_ticks()

        play_sound(level_sound)


def collect_gem():
    global combo
    global combo_multiplier
    global last_gem_time
    global combo_popup
    global combo_popup_timer
    global score

    now = pygame.time.get_ticks()

    if now - last_gem_time <= combo_timeout:
        combo += 1
    else:
        combo = 1

    last_gem_time = now

    combo_multiplier = min(
        5,
        1 + combo // 2
    )

    score += combo_multiplier

    combo_popup = f"COMBO x{combo_multiplier}"
    combo_popup_timer = now + 1000

    update_high_score()
    play_sound(gem_sound)


def update_combo():
    global combo
    global combo_multiplier

    if combo > 0:
        if (
            pygame.time.get_ticks()
            - last_gem_time
            > combo_timeout
        ):
            combo = 0
            combo_multiplier = 1


def draw_background():

    if level == 1 and level1_bg is not None:
        screen.blit(level1_bg, (0, 0))
        return

    if level == 2 and level2_bg is not None:
        screen.blit(level2_bg, (0, 0))
        return

    if level >= 3 and level3_bg is not None:
        screen.blit(level3_bg, (0, 0))
        return

    if level == 1:

        screen.fill((25, 45, 75))

        pygame.draw.circle(
            screen,
            (245, 230, 170),
            (720, 100),
            65
        )

        pygame.draw.circle(
            screen,
            (25, 45, 75),
            (750, 80),
            55
        )

        for x in range(0, WIDTH, 120):
            pygame.draw.polygon(
                screen,
                (20, 55, 55),
                [
                    (x, 600),
                    (x + 50, 400),
                    (x + 100, 600)
                ]
            )

        pygame.draw.rect(
            screen,
            (25, 70, 45),
            (0, 520, WIDTH, 80)
        )

    elif level == 2:

        screen.fill((38, 25, 55))

        pygame.draw.circle(
            screen,
            (220, 180, 150),
            (700, 100),
            65
        )

        for x in range(0, WIDTH, 130):
            pygame.draw.rect(
                screen,
                (20, 18, 30),
                (x, 390, 70, 210)
            )

            pygame.draw.polygon(
                screen,
                (20, 18, 30),
                [
                    (x, 390),
                    (x + 35, 330),
                    (x + 70, 390)
                ]
            )

        pygame.draw.rect(
            screen,
            (50, 25, 30),
            (0, 540, WIDTH, 60)
        )

    else:

        screen.fill((65, 18, 20))

        pygame.draw.circle(
            screen,
            (255, 90, 30),
            (700, 100),
            70
        )

        for x in range(0, WIDTH, 100):
            pygame.draw.polygon(
                screen,
                (110, 25, 15),
                [
                    (x, 600),
                    (x + 50, 380),
                    (x + 100, 600)
                ]
            )

        pygame.draw.rect(
            screen,
            (95, 25, 15),
            (0, 540, WIDTH, 60)
        )


def spawn_tower():

    if score < 10:
        gap = 210
    elif score < 25:
        gap = 180
    else:
        gap = 155

    top_height = random.randint(80, 310)

    towers.append({
        "x": WIDTH,
        "top_height": top_height,
        "gap": gap,
        "passed": False
    })

    gems.append({
        "x": WIDTH + 64,
        "y": top_height + gap // 2 - 16,
        "collected": False,
        "angle": random.random() * 6
    })


def draw_boss():

    pulse = int(
        math.sin(
            pygame.time.get_ticks() / 180
        ) * 8
    )

    pygame.draw.circle(
        screen,
        (80, 10, 100),
        (int(boss_x), int(boss_y)),
        80 + pulse
    )

    pygame.draw.polygon(
        screen,
        (75, 15, 95),
        [
            (boss_x - 20, boss_y - 25),
            (boss_x - 120, boss_y - 100),
            (boss_x - 80, boss_y - 5),
            (boss_x - 125, boss_y + 70),
            (boss_x - 10, boss_y + 30)
        ]
    )

    pygame.draw.polygon(
        screen,
        (75, 15, 95),
        [
            (boss_x + 20, boss_y - 25),
            (boss_x + 120, boss_y - 100),
            (boss_x + 80, boss_y - 5),
            (boss_x + 125, boss_y + 70),
            (boss_x + 10, boss_y + 30)
        ]
    )

    pygame.draw.ellipse(
        screen,
        (75, 20, 85),
        (
            boss_x - 65,
            boss_y - 65,
            130,
            130
        )
    )

    pygame.draw.polygon(
        screen,
        (105, 25, 110),
        [
            (boss_x - 40, boss_y - 55),
            (boss_x - 20, boss_y - 95),
            (boss_x - 5, boss_y - 60),
            (boss_x + 5, boss_y - 60),
            (boss_x + 20, boss_y - 95),
            (boss_x + 40, boss_y - 55)
        ]
    )

    pygame.draw.circle(
        screen,
        RED,
        (boss_x - 25, boss_y - 15),
        9
    )

    pygame.draw.circle(
        screen,
        RED,
        (boss_x + 25, boss_y - 15),
        9
    )

    pygame.draw.ellipse(
        screen,
        BLACK,
        (
            boss_x - 30,
            boss_y + 10,
            60,
            30
        )
    )

    bar_x = 540
    bar_y = 25
    bar_w = 310
    bar_h = 32

    pygame.draw.rect(
        screen,
        GOLD,
        (
            bar_x - 3,
            bar_y - 3,
            bar_w + 6,
            bar_h + 6
        )
    )

    pygame.draw.rect(
        screen,
        (50, 10, 10),
        (
            bar_x,
            bar_y,
            bar_w,
            bar_h
        )
    )

    hp_width = int(
        bar_w * boss_hp / boss_max_hp
    )

    pygame.draw.rect(
        screen,
        RED,
        (
            bar_x,
            bar_y,
            hp_width,
            bar_h
        )
    )

    text = font_small.render(
        f"DARK DRAGON   {boss_hp}/{boss_max_hp}",
        True,
        WHITE
    )

    screen.blit(
        text,
        (bar_x + 18, bar_y + 5)
    )


def draw_fireball(x, y, player=False):

    if player:
        colors = [CYAN, BLUE, WHITE]
    else:
        colors = [RED, ORANGE, YELLOW]

    pygame.draw.circle(
        screen,
        colors[0],
        (int(x), int(y)),
        12
    )

    pygame.draw.circle(
        screen,
        colors[1],
        (int(x), int(y)),
        8
    )

    pygame.draw.circle(
        screen,
        colors[2],
        (int(x), int(y)),
        4
    )


def draw_boss_hit_effects():

    now = pygame.time.get_ticks()

    for effect in boss_hit_effects[:]:

        age = now - effect["start"]

        if age > 450:
            boss_hit_effects.remove(effect)
            continue

        radius = 10 + int(age / 4)

        pygame.draw.circle(
            screen,
            YELLOW,
            (effect["x"], effect["y"]),
            radius,
            4
        )

        for i in range(8):

            angle = i * math.pi / 4
            length = 20 + age // 5

            x2 = effect["x"] + math.cos(angle) * length
            y2 = effect["y"] + math.sin(angle) * length

            pygame.draw.line(
                screen,
                ORANGE,
                (
                    effect["x"],
                    effect["y"]
                ),
                (
                    int(x2),
                    int(y2)
                ),
                3
            )


menu_time = 0


def draw_menu():

    global menu_time

    menu_time += 1

    if cover_bg is not None:

        screen.blit(
            cover_bg,
            (0, 0)
        )

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 0, 20, 55)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

    else:

        screen.fill(
            (12, 10, 30)
        )

        pygame.draw.circle(
            screen,
            (245, 230, 170),
            (720, 110),
            70
        )

        pygame.draw.circle(
            screen,
            (12, 10, 30),
            (750, 90),
            60
        )

        for x in range(0, WIDTH, 120):

            pygame.draw.rect(
                screen,
                (20, 18, 35),
                (
                    x,
                    390,
                    75,
                    210
                )
            )

            pygame.draw.polygon(
                screen,
                (20, 18, 35),
                [
                    (x, 390),
                    (x + 37, 340),
                    (x + 75, 390)
                ]
            )

    title = font_huge.render(
        "DRAGON'S FLIGHT",
        True,
        GOLD
    )

    screen.blit(
        title,
        (
            WIDTH // 2 - title.get_width() // 2,
            65
        )
    )

    subtitle = font.render(
        "CLASSIC REIMAGINED",
        True,
        WHITE
    )

    screen.blit(
        subtitle,
        (
            WIDTH // 2 - subtitle.get_width() // 2,
            150
        )
    )

    bob = int(
        math.sin(menu_time / 15) * 8
    )

    screen.blit(
        dragon_image,
        (
            WIDTH // 2 - 38,
            210 + bob
        )
    )

    pulse = int(
        math.sin(menu_time / 10) * 5
    )

    button = pygame.Rect(
        WIDTH // 2 - 150 - pulse,
        330 - pulse,
        300 + pulse * 2,
        70 + pulse * 2
    )

    pygame.draw.rect(
        screen,
        (45, 25, 70),
        button,
        border_radius=18
    )

    pygame.draw.rect(
        screen,
        GOLD,
        button,
        3,
        border_radius=18
    )

    start = font_big.render(
        "START GAME",
        True,
        GOLD
    )

    screen.blit(
        start,
        (
            WIDTH // 2 - start.get_width() // 2,
            342
        )
    )

    controls = font_small.render(
        "SPACE = FLAP     P = PAUSE     F = FIREBALL",
        True,
        WHITE
    )

    screen.blit(
        controls,
        (
            WIDTH // 2 - controls.get_width() // 2,
            445
        )
    )

    info = font_small.render(
        "Collect gems • Build combos • Defeat the Dark Dragon",
        True,
        CYAN
    )

    screen.blit(
        info,
        (
            WIDTH // 2 - info.get_width() // 2,
            480
        )
    )


def draw_hud():

    score_text = font.render(
        f"SCORE: {score}",
        True,
        WHITE
    )

    high_text = font_small.render(
        f"HIGH SCORE: {high_score}",
        True,
        GOLD
    )

    level_text = font.render(
        f"LEVEL {level}",
        True,
        CYAN
    )

    screen.blit(
        score_text,
        (20, 20)
    )

    screen.blit(
        high_text,
        (20, 58)
    )

    screen.blit(
        level_text,
        (
            WIDTH // 2
            - level_text.get_width() // 2,
            20
        )
    )

    hearts_label = font_small.render(
        "LIVES",
        True,
        WHITE
    )

    screen.blit(
        hearts_label,
        (
            WIDTH - 140,
            18
        )
    )

    draw_hearts(
        WIDTH - 140,
        45
    )

    if combo > 0:

        combo_text = font_small.render(
            f"COMBO x{combo_multiplier}",
            True,
            GOLD
        )

        combo_box = pygame.Rect(
            18,
            100,
            135,
            34
        )

        pygame.draw.rect(
            screen,
            (30, 20, 45),
            combo_box,
            border_radius=9
        )

        pygame.draw.rect(
            screen,
            GOLD,
            combo_box,
            2,
            border_radius=9
        )

        screen.blit(
            combo_text,
            (
                combo_box.x + 12,
                combo_box.y + 7
            )
        )


def draw_game_over():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (80, 0, 10, 160)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    title = font_huge.render(
        "GAME OVER",
        True,
        RED
    )

    screen.blit(
        title,
        (
            WIDTH // 2 - title.get_width() // 2,
            110
        )
    )

    score_text = font_big.render(
        f"SCORE: {score}",
        True,
        WHITE
    )

    high_text = font.render(
        f"HIGH SCORE: {high_score}",
        True,
        GOLD
    )

    screen.blit(
        score_text,
        (
            WIDTH // 2 - score_text.get_width() // 2,
            220
        )
    )

    screen.blit(
        high_text,
        (
            WIDTH // 2 - high_text.get_width() // 2,
            285
        )
    )

    restart = font.render(
        "PRESS R TO RESTART",
        True,
        WHITE
    )

    screen.blit(
        restart,
        (
            WIDTH // 2 - restart.get_width() // 2,
            400
        )
    )


def draw_victory():

    # Keep the original victory theme.
    # Only add subtle polish: glow, particles, border and dragon.

    screen.fill(
        (15, 35, 25)
    )

    # Soft green/gold glow behind the title
    glow = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    for radius, alpha in [
        (180, 12),
        (140, 18),
        (100, 25)
    ]:
        pygame.draw.circle(
            glow,
            (255, 190, 55, alpha),
            (WIDTH // 2, 125),
            radius
        )

    screen.blit(
        glow,
        (0, 0)
    )

    # Small magical sparkles
    now = pygame.time.get_ticks()

    for i in range(18):

        angle = (
            now / 900
            + i * 0.75
        )

        radius = 170 + (i % 4) * 35

        sparkle_x = (
            WIDTH // 2
            + math.cos(angle) * radius
        )

        sparkle_y = (
            280
            + math.sin(angle) * radius * 0.55
        )

        sparkle_size = 2 + (i % 3)

        pygame.draw.circle(
            screen,
            GOLD if i % 2 == 0 else CYAN,
            (
                int(sparkle_x),
                int(sparkle_y)
            ),
            sparkle_size
        )

    # Title glow
    title_glow = font_huge.render(
        "VICTORY!",
        True,
        (255, 220, 90)
    )

    glow_rect = title_glow.get_rect(
        center=(
            WIDTH // 2,
            130
        )
    )

    glow_layer = pygame.Surface(
        (
            title_glow.get_width() + 30,
            title_glow.get_height() + 30
        ),
        pygame.SRCALPHA
    )

    glow_layer.fill(
        (255, 190, 55, 18)
    )

    screen.blit(
        glow_layer,
        (
            glow_rect.x - 15,
            glow_rect.y - 15
        )
    )

    title = font_huge.render(
        "VICTORY!",
        True,
        GOLD
    )

    screen.blit(
        title,
        (
            WIDTH // 2 - title.get_width() // 2,
            90
        )
    )

    # Original subtitle
    subtitle = font_big.render(
        "LEGENDARY DRAGON",
        True,
        GREEN
    )

    screen.blit(
        subtitle,
        (
            WIDTH // 2 - subtitle.get_width() // 2,
            190
        )
    )

    # Small decorative line
    pygame.draw.line(
        screen,
        GOLD,
        (300, 245),
        (600, 245),
        2
    )

    pygame.draw.circle(
        screen,
        GOLD,
        (300, 245),
        4
    )

    pygame.draw.circle(
        screen,
        GOLD,
        (600, 245),
        4
    )

    message = font.render(
        "THE DARK DRAGON HAS FALLEN!",
        True,
        WHITE
    )

    screen.blit(
        message,
        (
            WIDTH // 2 - message.get_width() // 2,
            260
        )
    )

    # Keep the dragon image from the actual game
    dragon_bob = int(
        math.sin(now / 300) * 5
    )

    dragon_rect = dragon_image.get_rect(
        center=(
            WIDTH // 2,
            315 + dragon_bob
        )
    )

    screen.blit(
        dragon_image,
        dragon_rect
    )

    score_text = font.render(
        f"SCORE: {score}",
        True,
        WHITE
    )

    high_text = font.render(
        f"HIGH SCORE: {high_score}",
        True,
        GOLD
    )

    screen.blit(
        score_text,
        (
            WIDTH // 2 - score_text.get_width() // 2,
            365
        )
    )

    screen.blit(
        high_text,
        (
            WIDTH // 2 - high_text.get_width() // 2,
            405
        )
    )

    # Slightly polished restart panel
    restart_box = pygame.Rect(
        WIDTH // 2 - 180,
        455,
        360,
        58
    )

    pygame.draw.rect(
        screen,
        (25, 55, 40),
        restart_box,
        border_radius=14
    )

    pygame.draw.rect(
        screen,
        CYAN,
        restart_box,
        2,
        border_radius=14
    )

    restart = font.render(
        "PRESS R TO PLAY AGAIN",
        True,
        CYAN
    )

    screen.blit(
        restart,
        (
            WIDTH // 2 - restart.get_width() // 2,
            470
        )
    )


def draw_pause():

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (0, 0, 0, 160)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    title = font_huge.render(
        "PAUSED",
        True,
        GOLD
    )

    screen.blit(
        title,
        (
            WIDTH // 2 - title.get_width() // 2,
            210
        )
    )

    text = font.render(
        "PRESS P TO CONTINUE",
        True,
        WHITE
    )

    screen.blit(
        text,
        (
            WIDTH // 2 - text.get_width() // 2,
            320
        )
    )


def draw_level_transition():

    elapsed = (
        pygame.time.get_ticks()
        - level_transition_timer
    )

    if elapsed > level_transition_duration:
        return

    if level == 1:
        title = "LEVEL 1"
        subtitle = "ENCHANTED FOREST"
    elif level == 2:
        title = "LEVEL 2"
        subtitle = "CURSED CASTLE"
    else:
        title = "LEVEL 3"
        subtitle = "LAVA FORTRESS"

    box_width = 360
    box_height = 82

    box_x = WIDTH // 2 - box_width // 2
    box_y = 78

    panel = pygame.Surface(
        (box_width, box_height),
        pygame.SRCALPHA
    )

    panel.fill(
        (20, 10, 35, 220)
    )

    screen.blit(
        panel,
        (box_x, box_y)
    )

    pygame.draw.rect(
        screen,
        GOLD,
        (
            box_x,
            box_y,
            box_width,
            box_height
        ),
        3,
        border_radius=14
    )

    title_surface = font.render(
        title,
        True,
        GOLD
    )

    subtitle_surface = font_small.render(
        subtitle,
        True,
        WHITE
    )

    screen.blit(
        title_surface,
        (
            WIDTH // 2
            - title_surface.get_width() // 2,
            box_y + 8
        )
    )

    screen.blit(
        subtitle_surface,
        (
            WIDTH // 2
            - subtitle_surface.get_width() // 2,
            box_y + 48
        )
    )


def draw_countdown():

    elapsed = (
        pygame.time.get_ticks()
        - countdown_start_time
    )

    if elapsed < 1000:
        number = "3"
        color = GOLD
    elif elapsed < 2000:
        number = "2"
        color = ORANGE
    elif elapsed < 3000:
        number = "1"
        color = RED
    else:
        number = "GO!"
        color = GREEN

    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (5, 5, 20, 120)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    title = font_huge.render(
        number,
        True,
        color
    )

    screen.blit(
        title,
        (
            WIDTH // 2
            - title.get_width() // 2,
            220
        )
    )

    if number != "GO!":
        text = font.render(
            "GET READY!",
            True,
            WHITE
        )
    else:
        text = font_big.render(
            "FLY!",
            True,
            WHITE
        )

    screen.blit(
        text,
        (
            WIDTH // 2
            - text.get_width() // 2,
            330
        )
    )


def draw_game_objects():

    draw_background()

    for tower in towers:

        screen.blit(
            tower_top_image,
            (
                tower["x"],
                tower["top_height"] - 470
            )
        )

        screen.blit(
            tower_bottom_image,
            (
                tower["x"],
                tower["top_height"]
                + tower["gap"]
            )
        )

    for gem in gems:

        if not gem["collected"]:

            bob = int(
                math.sin(
                    gem["angle"]
                ) * 5
            )

            rotated = pygame.transform.rotate(
                gem_image,
                math.degrees(
                    math.sin(
                        gem["angle"]
                    )
                ) * 10
            )

            rect = rotated.get_rect(
                center=(
                    int(gem["x"] + 16),
                    int(
                        gem["y"]
                        + 16
                        + bob
                    )
                )
            )

            screen.blit(
                rotated,
                rect
            )

    draw_particles()
    draw_gem_particles()

    screen.blit(
        dragon_image,
        (
            dragon_x,
            int(dragon_y)
        )
    )

    draw_hud()


running = True

while running:

    clock.tick(FPS)

    now = pygame.time.get_ticks()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if menu:

                if event.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN
                ):
                    reset_game()

            elif game_over or victory:

                if event.key == pygame.K_r:
                    reset_game()

            else:

                if event.key == pygame.K_p:

                    if not countdown_active:
                        paused = not paused

                elif (
                    not paused
                    and not countdown_active
                ):

                    if event.key == pygame.K_SPACE:

                        dragon_velocity = flap_strength

                        play_sound(
                            flap_sound
                        )

                        particle_burst(
                            dragon_x + 10,
                            dragon_y + 30,
                            CYAN,
                            4
                        )

                    if (
                        event.key == pygame.K_f
                        and boss_fight
                    ):

                        if (
                            now
                            - last_player_shot
                            >= player_shot_delay
                        ):

                            player_fireballs.append({
                                "x": dragon_x + 65,
                                "y": dragon_y + 30
                            })

                            last_player_shot = now

                            play_sound(
                                fireball_sound
                            )

    if menu:

        draw_menu()

        pygame.display.flip()

        continue

    if game_over:

        draw_background()
        draw_game_over()

        pygame.display.flip()

        continue

    if victory:

        if not victory_sound_played:

            play_sound(
                victory_sound
            )

            victory_sound_played = True

        draw_victory()

        pygame.display.flip()

        continue

    if paused:

        draw_game_objects()
        draw_pause()

        pygame.display.flip()

        continue

    if countdown_active:

        elapsed = (
            now
            - countdown_start_time
        )

        draw_game_objects()
        draw_countdown()

        pygame.display.flip()

        if elapsed >= countdown_duration:

            countdown_active = False
            dragon_velocity = 0

            level_transition = True
            level_transition_timer = now

            play_sound(level_sound)

        continue

    update_level()

    if level_transition:

        if (
            now
            - level_transition_timer
            > level_transition_duration
        ):

            level_transition = False

    if (
        score >= 30
        and not boss_warning
        and not boss_fight
    ):

        boss_warning = True
        warning_start_time = now

        play_sound(
            warning_sound
        )

    if boss_warning and not boss_fight:

        screen.fill(
            (35, 5, 15)
        )

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        pulse = int(
            100
            + 80
            * abs(
                math.sin(
                    now / 150
                )
            )
        )

        overlay.fill(
            (120, 0, 0, pulse)
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        warning = font_huge.render(
            "WARNING!",
            True,
            RED
        )

        screen.blit(
            warning,
            (
                WIDTH // 2
                - warning.get_width() // 2,
                180
            )
        )

        text = font_big.render(
            "THE DARK DRAGON APPROACHES",
            True,
            WHITE
        )

        screen.blit(
            text,
            (
                WIDTH // 2
                - text.get_width() // 2,
                280
            )
        )

        if (
            now
            - warning_start_time
            > 2500
        ):

            boss_warning = False
            boss_fight = True
            boss_entering = True
            boss_enter_start = now

            boss_x = WIDTH + 150
            boss_y = 300

            boss_hp = boss_max_hp

            boss_fireballs.clear()
            player_fireballs.clear()

            last_boss_shot = now

        pygame.display.flip()

        continue

    if boss_fight:

        screen.fill(
            (30, 8, 45)
        )

        if boss_entering:

            progress = (
                now
                - boss_enter_start
            ) / 1200

            progress = min(
                1,
                progress
            )

            boss_x = (
                WIDTH + 150
                + (
                    760
                    - (
                        WIDTH
                        + 150
                    )
                ) * progress
            )

            if progress >= 1:
                boss_entering = False

        else:

            boss_y += (
                math.sin(
                    now / 500
                ) * 1.5
            )

            boss_y = max(
                120,
                min(
                    480,
                    boss_y
                )
            )

        if (
            not boss_entering
            and now
            - last_boss_shot
            >= boss_shot_delay
        ):

            boss_fireballs.append({
                "x": boss_x - 50,
                "y": boss_y
            })

            last_boss_shot = now

        for fireball in player_fireballs[:]:

            fireball["x"] += 10

            add_fire_trail(
                fireball["x"],
                fireball["y"]
            )

            if fireball["x"] > WIDTH:

                player_fireballs.remove(
                    fireball
                )

                continue

            fire_rect = pygame.Rect(
                fireball["x"] - 10,
                fireball["y"] - 10,
                20,
                20
            )

            boss_rect = pygame.Rect(
                boss_x - 65,
                boss_y - 65,
                130,
                130
            )

            if fire_rect.colliderect(
                boss_rect
            ):

                boss_hp -= 1

                boss_hit_effects.append({
                    "x": int(boss_x),
                    "y": int(boss_y),
                    "start": now
                })

                particle_burst(
                    boss_x,
                    boss_y,
                    ORANGE,
                    12
                )

                play_sound(
                    boss_hit_sound
                )

                player_fireballs.remove(
                    fireball
                )

                screen_shake = 7

                if boss_hp <= 0:

                    boss_hp = 0
                    victory = True

                    update_high_score()

        for fireball in boss_fireballs[:]:

            fireball["x"] -= 7

            add_fire_trail(
                fireball["x"],
                fireball["y"]
            )

            if fireball["x"] < -30:

                boss_fireballs.remove(
                    fireball
                )

                continue

            dragon_rect = pygame.Rect(
                dragon_x + 10,
                dragon_y + 8,
                55,
                45
            )

            fire_rect = pygame.Rect(
                fireball["x"] - 12,
                fireball["y"] - 12,
                24,
                24
            )

            if dragon_rect.colliderect(
                fire_rect
            ):

                lose_heart()

                boss_fireballs.remove(
                    fireball
                )

                if game_over:
                    update_high_score()

        dragon_velocity += gravity
        dragon_y += dragon_velocity

        if dragon_y < 0:

            dragon_y = 0
            dragon_velocity = 0

        if dragon_y > HEIGHT - 60:

            dragon_y = HEIGHT - 60

            lose_heart()

            dragon_velocity = flap_strength

            if game_over:
                update_high_score()

        update_fire_trails()

        draw_fire_trails()
        draw_boss()

        for fireball in player_fireballs:

            draw_fireball(
                fireball["x"],
                fireball["y"],
                True
            )

        for fireball in boss_fireballs:

            draw_fireball(
                fireball["x"],
                fireball["y"],
                False
            )

        screen.blit(
            dragon_image,
            (
                dragon_x,
                int(dragon_y)
            )
        )

        draw_boss_hit_effects()

        battle = font.render(
            "DARK DRAGON BATTLE",
            True,
            RED
        )

        screen.blit(
            battle,
            (20, 20)
        )

        instruction = font_small.render(
            "F = FIREBALL  •  5 HITS TO DEFEAT!",
            True,
            WHITE
        )

        screen.blit(
            instruction,
            (20, 58)
        )

        hearts_label = font_small.render(
            "LIVES",
            True,
            WHITE
        )

        screen.blit(
            hearts_label,
            (20, 95)
        )

        draw_hearts(
            20,
            120
        )

        pygame.display.flip()

        continue

    update_combo()

    dragon_velocity += gravity
    dragon_y += dragon_velocity

    if dragon_y < 0:

        dragon_y = 0
        dragon_velocity = 0

    if dragon_y > HEIGHT - 60:

        dragon_y = HEIGHT - 60

        lose_heart()

        dragon_velocity = flap_strength

        if game_over:
            update_high_score()

    spawn_timer += 1

    spawn_delay = max(
        70,
        115 - level * 10
    )

    if spawn_timer >= spawn_delay:

        spawn_tower()

        spawn_timer = 0

    if level == 1:
        speed = 4
    elif level == 2:
        speed = 5
    else:
        speed = 6

    dragon_rect = pygame.Rect(
        dragon_x + 10,
        dragon_y + 8,
        55,
        45
    )

    for tower in towers[:]:

        tower["x"] -= speed

        top_rect = pygame.Rect(
            tower["x"],
            0,
            TOWER_WIDTH,
            tower["top_height"]
        )

        bottom_y = (
            tower["top_height"]
            + tower["gap"]
        )

        bottom_rect = pygame.Rect(
            tower["x"],
            bottom_y,
            TOWER_WIDTH,
            HEIGHT - bottom_y
        )

        if (
            dragon_rect.colliderect(top_rect)
            or
            dragon_rect.colliderect(bottom_rect)
        ):

            lose_heart()

            particle_burst(
                dragon_x,
                dragon_y,
                RED,
                12
            )

            tower["x"] = -300

            if game_over:
                update_high_score()

        if (
            not tower["passed"]
            and tower["x"]
            + TOWER_WIDTH
            < dragon_x
        ):

            tower["passed"] = True

            score += 1

            update_high_score()

        if tower["x"] < -250:

            towers.remove(tower)

    for gem in gems[:]:

        gem["x"] -= speed
        gem["angle"] += 0.08

        if gem["collected"]:
            continue

        gem_rect = pygame.Rect(
            gem["x"],
            gem["y"],
            32,
            32
        )

        if dragon_rect.colliderect(
            gem_rect
        ):

            gem["collected"] = True

            collect_gem()

            gem_burst(
                gem["x"] + 16,
                gem["y"] + 16
            )

        if gem["x"] < -50:

            gems.remove(gem)

    update_particles()
    update_gem_particles()
    update_fire_trails()

    draw_game_objects()

    if level_transition:
        draw_level_transition()

    if screen_shake > 0:
        screen_shake -= 1

    if damage_flash > 0:

        flash = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        flash.fill(
            (255, 0, 0, damage_flash)
        )

        screen.blit(
            flash,
            (0, 0)
        )

        damage_flash -= 8

    pygame.display.flip()

pygame.quit()