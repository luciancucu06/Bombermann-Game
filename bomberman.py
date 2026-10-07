"""
============================================================================
  BOMBERMAN NEON EDITION
============================================================================
  CUPRINS (caută cu Ctrl+F textul dintre paranteze ca să sari la secțiune):
    [0] PANOU DE CONTROL ....... toate setările pe care le modifici la prezentare
    [1] CULORI ................. paleta de culori a jocului
    [2] AUDIO .................. încărcarea sunetelor
    [3] UTILITARE ............. fonturi (cache), lumini, particule
    [4] PROFIL & SALVARE ...... sistemul de nivel/bani/XP și salvarea în JSON
    [5] PERSONAJE & SPRITES ... lista de personaje și decuparea sprite-sheet-ului
    [6] HĂRȚI ................. hărțile fixe + generatorul aleatoriu
    [7] BONUSURI .............. obiectele care pică din pereți
    [8] BOMBĂ ................. logica bombei și a exploziei
    [9] JUCĂTOR & BOT ......... mișcarea, coliziunile, inteligența botului
    [10] RANDARE TEREN & HUD .. desenarea hărții și a interfeței de sus
    [11] MENIURI & ECRANE ..... butoane, login, meniu, magazin, hărți, personaje
    [12] BUCLA PRINCIPALĂ ..... funcția main() care leagă totul
============================================================================
"""

import pygame
import sys
import math
import json
import os
import random


# ===========================================================================
#  [0] PANOU DE CONTROL  —  modifică aici tot ce ai nevoie la prezentare
# ===========================================================================

# --- Rezoluție & dimensiunea hărții ---
SCREEN_W = 1920          # lățimea ecranului (se suprascrie automat la fullscreen)
SCREEN_H = 1080          # înălțimea ecranului
COLS       = 15          # numărul de coloane din hartă
ROWS       = 13          # numărul de rânduri din hartă
HUD_HEIGHT = 90          # înălțimea barei de sus (scor, vieți etc.)
BORDER     = 8           # marginea exterioară a hărții, în pixeli

# TILE = dimensiunea în pixeli a unui pătrățel. Se calculează singur ca să încapă.
TILE = min((SCREEN_W - BORDER * 2) // COLS,
           (SCREEN_H - BORDER * 2 - HUD_HEIGHT) // ROWS)
WIN_W = COLS * TILE + BORDER * 2
WIN_H = ROWS * TILE + BORDER * 2 + HUD_HEIGHT

# --- Fizică & timpi ---
FPS          = 60                  # cadre pe secundă
PLAYER_SPEED = float(TILE) * 2.8   # viteza de bază a jucătorului
BOMB_TIMER   = 2.8                 # secunde până explodează bomba
EXPLODE_TIME = 0.55                # cât durează animația de foc

# --- Spirala morții (sudden death) ---
SUDDEN_DEATH_START = 45.0          # după câte secunde începe să se umple harta
SUDDEN_DEATH_SPEED = 0.4           # cât de des apare un bloc nou

# --- Reguli de joc (statistici jucător) ---
STARTING_HP   = 3                  # viețile cu care pornește fiecare jucător
MAX_HP        = 5                  # plafonul de viață (din bonusuri)
MAX_RANGE     = 8                  # raza maximă a bombei
MAX_BOMBS     = 5                  # numărul maxim de bombe simultane
MAX_SPEED     = 2.0                # multiplicatorul maxim de viteză
SPEED_STEP    = 0.3                # cât adaugă un bonus de viteză
SHIELD_TIME   = 5.0                # durata scutului special (tasta E / RShift)
HURT_INVINC   = 1.5                # invincibilitate după ce ești lovit (secunde)

# --- Recompense ---
WALL_SCORE = 10                    # scor pentru un perete distrus
WALL_MONEY = 5                     # bani pentru un perete distrus
WALL_XP    = 15                    # XP pentru un perete distrus
KILL_SCORE = 100                   # scor pentru un adversar eliminat

# --- Bonusuri & bot ---
BONUS_CHANCE    = 0.45             # șansa să pice un bonus dintr-un perete (45%)
BOT_BOMB_CHANCE = 0.015            # șansa pe cadru ca botul să pună o bombă

# Preț în magazin
COST_RANGE = 50
COST_BOMBS = 100


# ===========================================================================
#  [1] CULORI  —  stil clasic Bomberman cu accente neon
# ===========================================================================
C_BG         = (30,  80,  30)
C_FLOOR      = (60, 140,  50)
C_FLOOR2     = (55, 130,  45)
C_WALL_HARD  = (130, 130, 140)
C_WALL_HARD2 = (110, 110, 120)
C_WALL_SOFT  = (160, 110,  60)
C_WALL_SOFT2 = (140,  90,  40)
C_HUD_BG     = (20,  20,  35)
C_TEXT       = (210, 210, 210)
C_NEON_BLUE  = (0, 180, 255)
C_NEON_PURP  = (180, 50, 255)
C_MENU_BG    = (10, 15, 25)

# Culori bonusuri
C_BONUS_HP    = (255, 80,  80)   # roșu  = viață
C_BONUS_RANGE = (255, 200,  0)   # galben = rază
C_BONUS_BOMBS = (0,   220, 120)  # verde = bombe extra
C_BONUS_SPEED = (0,   180, 255)  # albastru = viteză


# ===========================================================================
#  [2] AUDIO  —  încărcare sigură (jocul merge și fără placă de sunet)
# ===========================================================================
AUDIO_OK = False
try:
    pygame.mixer.init()
    AUDIO_OK = True
except Exception:
    AUDIO_OK = False

if AUDIO_OK:
    try:
        SND_PLACE   = pygame.mixer.Sound("place.wav")
        SND_EXPLODE = pygame.mixer.Sound("explode.wav")
        SND_DIE     = pygame.mixer.Sound("die.wav")
    except Exception:
        SND_PLACE = SND_EXPLODE = SND_DIE = None
else:
    SND_PLACE = SND_EXPLODE = SND_DIE = None

def play_sound(snd):
    if snd:
        snd.play()


# ===========================================================================
#  [3] UTILITARE  —  fonturi (cu cache), lumini dinamice, particule
# ===========================================================================

# --- Cache de fonturi (FIX: nu mai construim un font nou în fiecare cadru) ---
_FONT_CACHE = {}
def get_font(size, bold=False, name="Arial"):
    """Întoarce un font, creându-l o singură dată și reutilizându-l apoi."""
    key = (name, size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(name, size, bold=bold)
    return _FONT_CACHE[key]


def make_light(radius, max_color):
    """Creează o suprafață circulară cu gradient pentru iluminare."""
    surf = pygame.Surface((radius * 2, radius * 2))
    surf.fill((0, 0, 0))
    for r in range(radius, 0, -3):
        intensity = (1.0 - (r / radius)) ** 1.5   # curbă neliniară = glow natural
        c = (int(max_color[0] * intensity),
             int(max_color[1] * intensity),
             int(max_color[2] * intensity))
        pygame.draw.circle(surf, c, (radius, radius), r)
    return surf

# Luminile se pot construi de la pornire (nu au nevoie de pygame.init).
L_PLAYER = make_light(int(TILE * 2.5), (90, 90, 100))
L_BOMB   = make_light(int(TILE * 2.2), (180, 50, 0))
L_EXPL   = make_light(int(TILE * 3.8), (255, 120, 30))


class Particle:
    """Bucățică de moloz aruncată când se distruge un perete."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-180, 180)   # viteză explozivă pe X
        self.vy = random.uniform(-400, -100)  # sare în sus pe Y
        self.color = color
        self.life = random.uniform(0.4, 0.8)

    def update(self, dt):
        self.vy += 900 * dt   # gravitație
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface, ox, oy):
        if self.life > 0:
            size = max(2, int(self.life * 8))
            pygame.draw.rect(surface, self.color,
                             (int(ox + self.x), int(oy + self.y), size, size))


# ===========================================================================
#  [4] PROFIL & SALVARE  —  nivel, XP, bani; salvare în profiles.json
# ===========================================================================
PROFILE_FILE = "profiles.json"
PROFILE = {}

def load_profile(username):
    global PROFILE
    username = username.strip().upper()
    default_profile = {
        "name": username, "level": 1, "xp": 0, "xp_needed": 100,
        "money": 0, "p1_max_bombs": 1, "p1_bomb_range": 2,
        "p2_max_bombs": 1, "p2_bomb_range": 2
    }
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            try:
                data = json.load(f)
                if username in data:
                    PROFILE = data[username]
                    return
            except json.JSONDecodeError:
                pass
    PROFILE = default_profile

def save_profile():
    data = {}
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    data[PROFILE["name"]] = PROFILE
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def apply_earnings(money, xp):
    """
    Adaugă bani/XP în memorie și gestionează urcarea în nivel.
    FIX: NU mai scrie pe disc aici — salvarea se face o singură dată la
    finalul rundei (vezi save_profile() din bucla principală). Înainte,
    salvarea la fiecare perete distrus producea lag.
    """
    PROFILE["money"] += money
    PROFILE["xp"] += xp
    if PROFILE["xp"] >= PROFILE["xp_needed"]:
        PROFILE["level"] += 1
        PROFILE["xp"] -= PROFILE["xp_needed"]
        PROFILE["xp_needed"] = int(PROFILE["xp_needed"] * 1.5)


# ===========================================================================
#  [5] PERSONAJE & SPRITES  —  decuparea sprite-sheet-ului „Bombermannn.png"
# ===========================================================================
_ROWS = [0, 26, 59, 94, 125, 158, 190, 224, 257]
_COLS = [0, 31, 61, 93, 127, 161, 194, 224, 258, 290, 321]

CHARACTERS = [
    {"name": "Alb (Clasic)", "color": (255, 255, 255)},
    {"name": "Roșu",         "color": (255,  50,  50)},
    {"name": "Albastru",     "color": ( 50,  50, 255)},
    {"name": "Verde",        "color": ( 50, 255,  50)},
    {"name": "Auriu",        "color": (255, 215,   0)},
    {"name": "Cyan",         "color": (  0, 255, 255)},
    {"name": "Roz",          "color": (255,  50, 200)},
    {"name": "Întunecat",    "color": (120, 120, 120)},
]

def load_char_sprites(sheet, char_color):
    y0 = _ROWS[0]; h = _ROWS[1] - y0
    def spr(c):
        x0 = _COLS[c]; w = _COLS[c + 1] - x0
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.blit(sheet, (0, 0), (x0, y0, w, h))
        s = pygame.transform.scale(s, (TILE, TILE))
        if char_color != (255, 255, 255):
            tint = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            tint.fill((*char_color, 255))
            s.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return s
    def spr_flip(c):
        return pygame.transform.flip(spr(c), True, False)
    return {
        'down':  [spr(0), spr(1), spr(2)],
        'right': [spr(3), spr(4), spr(5)],
        'up':    [spr(6), spr(7), spr(8)],
        'left':  [spr_flip(3), spr_flip(4), spr_flip(5)],
    }


# ===========================================================================
#  [6] HĂRȚI  —  hărți fixe (P=jucător1, Q=jucător2, B=bot, X=perete moale)
# ===========================================================================
MAPS = {
    "Clasic": [
        "###############",
        "#P.XX.X.X.XX.Q#",
        "#X#X#X#X#X#X#X#",
        "#XXXXX.B.XXXXX#",
        "#X#.#X#X#X#.#X#",
        "#XX.XXXBXXX.XX#",
        "#X#X#X#.#X#X#X#",
        "#XX.XXXBXXX.XX#",
        "#X#.#X#X#X#.#X#",
        "#XXXXX...XXXXX#",
        "#X#X#X#X#X#X#X#",
        "#..XX.X.X.XX..#",
        "###############",
    ],
    "Retro Arcade": [
        "###############",
        "#P.XXXXXXXXXXQ#",
        "#.X#X#X#X#X#X.#",
        "#XXXXXXXXXXXXX#",
        "#X#X#X#X#X#X#X#",
        "#XXXXXXBXXXXXX#",
        "#X#X#X#X#X#X#X#",
        "#XXXXXXBXXXXXX#",
        "#X#X#X#X#X#X#X#",
        "#XXXXXXXXXXXXX#",
        "#.X#X#X#X#X#X.#",
        "#QXXXXXXXXXX.P#",
        "###############",
    ],
    "Aleatoriu": None,
}

def generate_random_map():
    template = []
    template.append("#" * COLS)
    for r in range(1, ROWS - 1):
        row = "#"
        for c in range(1, COLS - 1):
            if (r <= 2 and c <= 2) or (r <= 2 and c >= COLS - 3) or \
               (r >= ROWS - 3 and c <= 2) or (r >= ROWS - 3 and c >= COLS - 3):
                row += "."
            elif r % 2 == 0 and c % 2 == 0:
                row += "#"
            else:
                row += "X" if random.random() < 0.40 else "."
        row += "#"
        template.append(row)
    template.append("#" * COLS)

    lines = list(template)
    lines[1] = "P" + lines[1][1:]
    last_row = list(lines[ROWS - 2]); last_row[COLS - 2] = "Q"
    lines[ROWS - 2] = "".join(last_row)
    mid_r = ROWS // 2; mid_c = COLS // 2
    row_list = list(lines[mid_r]); row_list[mid_c] = "B"
    lines[mid_r] = "".join(row_list)
    return lines

def build_map(template):
    """Transformă șablonul text în grilă logică: H=tare, S=moale, .=liber."""
    grid = []
    p1_pos = (1, 1); p2_pos = (COLS - 2, ROWS - 2); bots_pos = []
    for r, row in enumerate(template[:ROWS]):
        line = []
        for c in range(COLS):
            ch = row[c] if c < len(row) else '.'
            if ch == '#':   line.append('H')
            elif ch == 'X': line.append('S')
            elif ch == 'P': line.append('.'); p1_pos = (c, r)
            elif ch == 'Q': line.append('.'); p2_pos = (c, r)
            elif ch == 'B': line.append('.'); bots_pos.append((c, r))
            else:           line.append('.')
        grid.append(line)
    return grid, p1_pos, p2_pos, bots_pos

def get_spiral_coords():
    """Ordinea în care se umple harta în spirală la sudden death."""
    coords = []
    l, r, t, b = 1, COLS - 2, 1, ROWS - 2
    while l <= r and t <= b:
        for i in range(l, r + 1): coords.append((i, t))
        t += 1
        for i in range(t, b + 1): coords.append((r, i))
        r -= 1
        if t <= b:
            for i in range(r, l - 1, -1): coords.append((i, b))
            b -= 1
        if l <= r:
            for i in range(b, t - 1, -1): coords.append((l, i))
            l += 1
    return coords


# ===========================================================================
#  [7] BONUSURI  —  obiectele care pică uneori dintr-un perete distrus
# ===========================================================================
BONUS_TYPES = ['hp', 'range', 'bombs', 'speed']

class Bonus:
    def __init__(self, col, row, bonus_type):
        self.col = col
        self.row = row
        self.type = bonus_type
        self.anim_t = 0.0

    def update(self, dt):
        self.anim_t += dt * 3.0

    def draw(self, surface, ox, oy):
        x = ox + self.col * TILE
        y = oy + self.row * TILE
        cx = x + TILE // 2
        cy = y + TILE // 2

        pulse = 0.85 + 0.15 * math.sin(self.anim_t)
        size = int(TILE * 0.82 * pulse)
        half = size // 2

        if self.type == 'hp':
            color = C_BONUS_HP; dark = (180, 30, 30); label = "HP"
        elif self.type == 'range':
            color = C_BONUS_RANGE; dark = (180, 130, 0); label = "RNG"
        elif self.type == 'bombs':
            color = C_BONUS_BOMBS; dark = (0, 150, 70); label = "BOM"
        else:
            color = C_BONUS_SPEED; dark = (0, 100, 180); label = "SPD"

        rect = pygame.Rect(cx - half, cy - half, size, size)
        pygame.draw.rect(surface, dark, rect, border_radius=6)
        inner = rect.inflate(-4, -4)
        pygame.draw.rect(surface, color, inner, border_radius=5)

        # FIX: font luat din cache, nu recreat de fiecare dată
        fnt = get_font(int(TILE * 0.28), bold=True)
        txt = fnt.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=(cx, cy)))

    def apply(self, player):
        if self.type == 'hp':
            player.hp = min(player.hp + 1, MAX_HP)
        elif self.type == 'range':
            player.bomb_range = min(player.bomb_range + 1, MAX_RANGE)
        elif self.type == 'bombs':
            player.max_bombs = min(player.max_bombs + 1, MAX_BOMBS)
        elif self.type == 'speed':
            player.speed_mult = min(player.speed_mult + SPEED_STEP, MAX_SPEED)

def maybe_spawn_bonus(col, row):
    if random.random() < BONUS_CHANCE:
        return Bonus(col, row, random.choice(BONUS_TYPES))
    return None

def render_map_preview(template, preview_w=480, preview_h=360):
    tile_w = preview_w // COLS
    tile_h = preview_h // ROWS
    surf = pygame.Surface((COLS * tile_w, ROWS * tile_h))
    surf.fill(C_BG)
    COLOR_MAP = {'H': C_WALL_HARD, 'S': C_WALL_SOFT, '.': C_FLOOR,
                 'P': C_FLOOR, 'Q': C_FLOOR, 'B': C_FLOOR,
                 '#': C_WALL_HARD, 'X': C_WALL_SOFT}
    for r, row in enumerate(template[:ROWS]):
        for c in range(COLS):
            ch = row[c] if c < len(row) else '.'
            color = COLOR_MAP.get(ch, C_FLOOR)
            pygame.draw.rect(surf, color, (c * tile_w, r * tile_h, tile_w - 1, tile_h - 1))
            if ch == 'P':
                pygame.draw.circle(surf, (255, 255, 255),
                                   (c * tile_w + tile_w // 2, r * tile_h + tile_h // 2), tile_w // 3)
            elif ch == 'Q':
                pygame.draw.circle(surf, CHARACTERS[1]['color'],
                                   (c * tile_w + tile_w // 2, r * tile_h + tile_h // 2), tile_w // 3)
            elif ch == 'B':
                pygame.draw.circle(surf, CHARACTERS[7]['color'],
                                   (c * tile_w + tile_w // 2, r * tile_h + tile_h // 2), tile_w // 3)
    pygame.draw.rect(surf, C_NEON_BLUE, (0, 0, COLS * tile_w, ROWS * tile_h), 2)
    return surf


# ===========================================================================
#  [8] BOMBĂ  —  numărătoare, explozie în cruce, daune, reacții în lanț
# ===========================================================================
class Bomb:
    def __init__(self, col, row, owner, bomb_range):
        self.col = col; self.row = row
        self.owner = owner
        self.bomb_range = bomb_range
        self.timer = BOMB_TIMER
        self.exploding = False
        self.explode_timer = 0.0
        self.cells = []
        play_sound(SND_PLACE)

    def update(self, dt, grid, bombs, players, bonuses, particles, shake_state):
        if self.exploding:
            self.explode_timer -= dt
            return self.explode_timer <= 0
        self.timer -= dt
        if self.timer <= 0:
            self._explode(grid, bombs, players, bonuses, particles, shake_state)
        return False

    def _explode(self, grid, bombs, players, bonuses, particles, shake_state):
        self.exploding = True
        self.explode_timer = EXPLODE_TIME
        play_sound(SND_EXPLODE)
        self.cells = [(self.col, self.row, 'center')]
        shake_state[0] = 0.4   # pornește cutremurul camerei

        new_bonuses = []

        for dc, dr, mid, end in [(1, 0, 'h', 'end_r'), (-1, 0, 'h', 'end_l'),
                                 (0, 1, 'v', 'end_d'), (0, -1, 'v', 'end_u')]:
            for dist in range(1, self.bomb_range + 1):
                c = self.col + dc * dist; r = self.row + dr * dist
                if not (0 <= c < COLS and 0 <= r < ROWS):
                    break
                cell = grid[r][c]
                if cell == 'H':
                    break
                tip = end if dist == self.bomb_range else mid
                if cell == 'S':
                    self.cells.append((c, r, end))
                    grid[r][c] = '.'
                    if hasattr(self.owner, 'score'):
                        self.owner.score += WALL_SCORE
                    # FIX: banii/XP merg în profil DOAR dacă peretele e spart de
                    # un jucător real, nu de un bot. Și fără scriere pe disc aici.
                    if not getattr(self.owner, 'is_bot', False):
                        apply_earnings(WALL_MONEY, WALL_XP)

                    # particule de moloz
                    for _ in range(12):
                        c_col = random.choice([(160, 160, 160), (130, 140, 150), (90, 95, 105)])
                        particles.append(Particle(c * TILE + TILE / 2, r * TILE + TILE / 2, c_col))

                    bonus = maybe_spawn_bonus(c, r)
                    if bonus:
                        new_bonuses.append(bonus)
                    break
                self.cells.append((c, r, tip))

        blast = {(c, r) for c, r, _ in self.cells}

        # bonusurile prinse în explozie dispar; cele noi (din pereți) rămân
        bonuses[:] = [b for b in bonuses if (b.col, b.row) not in blast]
        bonuses.extend(new_bonuses)

        # daune jucători
        for p in players:
            if not p.alive:
                continue
            pc = int(p.px / TILE + 0.5); pr = int(p.py / TILE + 0.5)
            if (pc, pr) in blast and p.invincible <= 0:
                p.hp -= 1; p.hurt_flash = 0.7; p.invincible = HURT_INVINC
                if p.hp <= 0:
                    p.alive = False
                    play_sound(SND_DIE)
                    if hasattr(self.owner, 'score') and p != self.owner:
                        self.owner.score += KILL_SCORE

        # reacție în lanț: bombele atinse explodează imediat
        for b in bombs:
            if b is not self and not b.exploding and (b.col, b.row) in blast:
                b.timer = 0

    def draw(self, surface, ox, oy):
        col = self.owner.color
        if not self.exploding:
            pulse = abs((self.timer % 0.5) - 0.25) / 0.25
            r = int(TILE * 0.18 + pulse * TILE * 0.07)
            cx = int(ox + self.col * TILE + TILE / 2)
            cy = int(oy + self.row * TILE + TILE / 2)
            pygame.draw.circle(surface, (20, 20, 20), (cx, cy), r + 2)
            pygame.draw.circle(surface, col, (cx, cy), r)
        else:
            t = 1.0 - self.explode_timer / EXPLODE_TIME
            alpha = int(255 * (1.0 - t * 0.5))
            for (ec, er, tip) in self.cells:
                ex = ox + ec * TILE; ey = oy + er * TILE
                s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                pygame.draw.rect(s, (*col, alpha), (0, 0, TILE, TILE))
                surface.blit(s, (ex, ey))


# ===========================================================================
#  [9] JUCĂTOR & BOT  —  mișcare, coliziuni, bonusuri, AI simplu
# ===========================================================================
class Player:
    is_bot = False   # FIX: marcaj sigur pentru bot, în loc de comparație pe nume

    def __init__(self, name, color, col, row, keys, anims, max_bombs, bomb_range):
        self.name = name; self.color = color
        self.hp = STARTING_HP; self.score = 0; self.alive = True
        self.px = float(col * TILE); self.py = float(row * TILE)
        self.col = col; self.row = row
        self.keys = keys; self.anims = anims
        self.facing = 'down'
        self.walk_t = 0.0; self.frame = 1; self.moving = False
        self.bomb_range = bomb_range
        self.max_bombs  = max_bombs
        self.speed_mult = 1.0
        self.invincible = 0.0; self.hurt_flash = 0.0
        self.bomb_pressed = False
        self.special_used = False
        self.key_special = keys[5] if len(keys) > 5 else None
        self.bonus_msg = ""
        self.bonus_msg_t = 0.0

    @property
    def image(self):
        return self.anims[self.facing][self.frame % 3]
    def tile_col(self):
        return int((self.px + TILE / 2) // TILE)
    def tile_row(self):
        return int((self.py + TILE / 2) // TILE)

    def collect_bonuses(self, bonuses):
        tc = self.tile_col(); tr = self.tile_row()
        for b in bonuses[:]:
            if b.col == tc and b.row == tr:
                b.apply(self)
                bonuses.remove(b)
                msgs = {'hp': '+1 ❤ Viata!', 'range': '+1 ★ Raza!',
                        'bombs': '+1 Bomba!', 'speed': '+Viteza!'}
                self.bonus_msg = msgs.get(b.type, 'Bonus!')
                self.bonus_msg_t = 2.0

    def handle_input(self, keys_state, grid, bombs, dt):
        if not self.alive:
            return None
        if self.key_special and keys_state[self.key_special] and not self.special_used:
            self.invincible = SHIELD_TIME
            self.special_used = True

        ku, kd, kl, kr, kb = self.keys[:5]
        dx = dy = 0
        if keys_state[ku]: dy -= 1; self.facing = 'up'
        if keys_state[kd]: dy += 1; self.facing = 'down'
        if keys_state[kl]: dx -= 1; self.facing = 'left'
        if keys_state[kr]: dx += 1; self.facing = 'right'

        if dx != 0 or dy != 0:
            if dx != 0 and dy != 0:
                length = math.hypot(dx, dy)
                dx /= length; dy /= length
            self._move(dx, dy, grid, bombs, dt)
            self.moving = True
        else:
            self.moving = False

        new_bomb = None
        if keys_state[kb]:
            if not self.bomb_pressed:
                self.bomb_pressed = True
                tc = self.tile_col(); tr = self.tile_row()
                active = sum(1 for b in bombs if b.owner is self and not b.exploding)
                bomb_cells = [(b.col, b.row) for b in bombs]
                if active < self.max_bombs and (tc, tr) not in bomb_cells:
                    new_bomb = Bomb(tc, tr, self, self.bomb_range)
        else:
            self.bomb_pressed = False
        return new_bomb

    def _move(self, dx, dy, grid, bombs, dt):
        speed = PLAYER_SPEED * dt * self.speed_mult
        hw = TILE * 0.5; hh = TILE * 0.5
        offset_x = (TILE - hw) / 2; offset_y = (TILE - hh) / 2
        curr_rect = pygame.Rect(self.px + offset_x, self.py + offset_y, hw, hh)
        # bombele pe care stai deja sunt ignorate până cobori de pe ele
        ignored_bombs = [b for b in bombs if not b.exploding and
                         curr_rect.colliderect(pygame.Rect(b.col * TILE, b.row * TILE, TILE, TILE))]

        def get_collisions(test_x, test_y):
            rect = pygame.Rect(test_x + offset_x, test_y + offset_y, hw, hh)
            cols = []
            min_c = max(0, int(rect.left // TILE)); max_c = min(COLS - 1, int(rect.right // TILE))
            min_r = max(0, int(rect.top // TILE)); max_r = min(ROWS - 1, int(rect.bottom // TILE))
            for r in range(min_r, max_r + 1):
                for c in range(min_c, max_c + 1):
                    if grid[r][c] in ('H', 'S'):
                        cols.append(pygame.Rect(c * TILE, r * TILE, TILE, TILE))
            for b in bombs:
                if not b.exploding and b not in ignored_bombs:
                    b_rect = pygame.Rect(b.col * TILE, b.row * TILE, TILE, TILE)
                    if rect.colliderect(b_rect):
                        cols.append(b_rect)
            return cols

        if dx != 0:
            nx = self.px + dx * speed
            cols = get_collisions(nx, self.py)
            if not cols:
                self.px = nx
            else:
                if dx > 0: self.px = min(c.left for c in cols) - offset_x - hw - 0.01
                else:      self.px = max(c.right for c in cols) - offset_x + 0.01
        if dy != 0:
            ny = self.py + dy * speed
            cols = get_collisions(self.px, ny)
            if not cols:
                self.py = ny
            else:
                if dy > 0: self.py = min(c.top for c in cols) - offset_y - hh - 0.01
                else:      self.py = max(c.bottom for c in cols) - offset_y + 0.01

        self.px = max(0, min(self.px, (COLS - 1) * TILE))
        self.py = max(0, min(self.py, (ROWS - 1) * TILE))
        self.col = self.tile_col(); self.row = self.tile_row()

    def update(self, dt):
        if not self.alive:
            return
        if self.invincible > 0: self.invincible -= dt
        if self.hurt_flash > 0: self.hurt_flash -= dt
        if self.bonus_msg_t > 0: self.bonus_msg_t -= dt
        if self.moving:
            self.walk_t += dt * 10
            self.frame = int(self.walk_t) % 3
        else:
            self.walk_t = 0; self.frame = 1

    def draw(self, surface, ox, oy):
        if not self.alive:
            return
        if self.hurt_flash > 0 and int(self.hurt_flash * 14) % 2 == 0:
            return  # clipește când e lovit
        x = int(ox + self.px); y = int(oy + self.py)
        surface.blit(self.image, (x, y))
        if self.invincible > 0 and self.hurt_flash <= 0:
            pygame.draw.circle(surface, (255, 215, 0),
                               (x + TILE // 2, y + TILE // 2), TILE // 2 + 3, 3)

    def draw_bonus_msg(self, surface, ox, oy, font):
        if self.bonus_msg_t > 0 and self.bonus_msg:
            alpha = min(255, int(self.bonus_msg_t * 200))
            x = int(ox + self.px) + TILE // 2
            y = int(oy + self.py) - int((2.0 - self.bonus_msg_t) * 30) - 10
            txt = font.render(self.bonus_msg, True, (255, 230, 50))
            txt.set_alpha(alpha)
            surface.blit(txt, txt.get_rect(center=(x, y)))


class Bot(Player):
    is_bot = True   # FIX: identificat prin acest marcaj, nu prin nume

    def __init__(self, color, col, row, anims):
        super().__init__("BOT", color, col, row, (0, 0, 0, 0, 0, 0), anims, 1, 2)
        self.bot_timer = 0
        self.bot_dir = (0, 0)

    def handle_input(self, keys_state, grid, bombs, dt):
        if not self.alive:
            return None
        self.bot_timer -= dt
        if self.bot_timer <= 0:
            self.bot_dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
            self.bot_timer = random.uniform(0.3, 1.2)
        dx, dy = self.bot_dir
        if dx != 0 or dy != 0:
            self._move(dx, dy, grid, bombs, dt)
            self.moving = True
        else:
            self.moving = False
        if random.random() < BOT_BOMB_CHANCE:
            tc = self.tile_col(); tr = self.tile_row()
            active = sum(1 for b in bombs if b.owner is self and not b.exploding)
            bomb_cells = [(b.col, b.row) for b in bombs]
            if active < self.max_bombs and (tc, tr) not in bomb_cells:
                return Bomb(tc, tr, self, self.bomb_range)
        return None


# ===========================================================================
#  [10] RANDARE TEREN & HUD
# ===========================================================================
def build_bg(grid, ox, oy):
    """Desenează fundalul fix (podea + pereți tari). Se reface doar când harta se schimbă."""
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    surf.fill(C_BG)
    border_rect = pygame.Rect(ox - BORDER, oy - BORDER, COLS * TILE + BORDER * 2, ROWS * TILE + BORDER * 2)
    pygame.draw.rect(surf, (80, 60, 30), border_rect)
    pygame.draw.rect(surf, (50, 35, 15), border_rect, BORDER)

    for row in range(ROWS):
        for col in range(COLS):
            x = ox + col * TILE; y = oy + row * TILE
            cell = grid[row][col]
            if cell == 'H':
                pygame.draw.rect(surf, (150, 150, 150), (x, y, TILE, TILE))
                pygame.draw.rect(surf, (220, 220, 220), (x, y, TILE, 4))
                pygame.draw.rect(surf, (220, 220, 220), (x, y, 4, TILE))
                pygame.draw.rect(surf, (90, 90, 90), (x, y + TILE - 4, TILE, 4))
                pygame.draw.rect(surf, (90, 90, 90), (x + TILE - 4, y, 4, TILE))
                pygame.draw.rect(surf, (110, 110, 110), (x + 8, y + 8, TILE - 16, TILE - 16))
            else:
                floor_col = (70, 170, 50) if (row + col) % 2 == 0 else (60, 150, 40)
                pygame.draw.rect(surf, floor_col, (x, y, TILE, TILE))
    return surf

def draw_dynamic_tiles(surface, grid, ox, oy):
    """Desenează pereții moi (S), care se distrug în timpul jocului."""
    for row in range(ROWS):
        for col in range(COLS):
            cell = grid[row][col]
            x = ox + col * TILE; y = oy + row * TILE
            if cell == 'S':
                pygame.draw.rect(surface, (160, 160, 160), (x, y, TILE, TILE))
                h = TILE // 3
                for i in range(3):
                    cy = y + i * h
                    pygame.draw.rect(surface, (130, 140, 150), (x, cy, TILE, h - 2))
                    if i % 2 == 0:
                        pygame.draw.line(surface, (90, 95, 105), (x + TILE // 2, cy), (x + TILE // 2, cy + h - 2), 2)
                    else:
                        pygame.draw.line(surface, (90, 95, 105), (x + TILE // 4, cy), (x + TILE // 4, cy + h - 2), 2)
                        pygame.draw.line(surface, (90, 95, 105), (x + 3 * TILE // 4, cy), (x + 3 * TILE // 4, cy + h - 2), 2)

def draw_hud(surface, players, font_big, font_sm, font_title, paused, game_over, sudden_death):
    pygame.draw.rect(surface, C_HUD_BG, (0, 0, SCREEN_W, HUD_HEIGHT))
    pygame.draw.line(surface, C_NEON_BLUE, (0, HUD_HEIGHT - 2), (SCREEN_W, HUD_HEIGHT - 2), 2)

    real_players = [p for p in players if not p.is_bot]   # FIX: marcaj, nu nume
    n = len(real_players)
    panel_w = SCREEN_W // max(n, 1)

    for i, p in enumerate(real_players):
        x = i * panel_w + 20
        surface.blit(font_big.render(p.name, True, p.color), (x, 8))
        for h in range(5):
            if h >= 3 and h >= p.hp:
                break
            c = p.color if h < p.hp else (40, 40, 50)
            cx = x + h * 28 + 16; cy = 52
            pygame.draw.circle(surface, c, (cx, cy), 10)
        surface.blit(font_sm.render(f"Scor: {p.score}", True, C_TEXT), (x + 160, 8))

        spec_key = "E" if i == 0 else "RShift"
        if not p.special_used:
            spec_txt = f"[{spec_key}] Scut 5s"; spec_col = (255, 215, 0)
        else:
            spec_txt = "Scut folosit"; spec_col = (100, 100, 100)
        surface.blit(font_sm.render(spec_txt, True, spec_col), (x + 160, 30))
        surface.blit(font_sm.render(
            f"Bombe:{p.max_bombs}  Raza:{p.bomb_range}  Vit:{p.speed_mult:.1f}x",
            True, C_TEXT), (x + 160, 54))

    msg_surface = None
    if game_over:
        alive = [p for p in real_players if p.alive]
        if len(alive) == 1:
            txt = f"🏆  {alive[0].name} a câștigat!   R = Meniu"; col = alive[0].color
        elif len(alive) == 0:
            txt = "Nimeni nu a câștigat!   R = Meniu"; col = (200, 200, 200)
        else:
            txt = "EGALITATE!   R = Meniu"; col = (255, 220, 50)
        msg_surface = font_title.render(txt, True, col)
    elif sudden_death:
        msg_surface = font_big.render("⚠  SPIRALA MORȚII  ⚠", True, (255, 50, 50))
    elif paused:
        msg_surface = font_big.render("PAUZA  —  SPACE pentru a continua", True, (255, 220, 50))

    if msg_surface:
        rect = msg_surface.get_rect(center=(SCREEN_W // 2, HUD_HEIGHT // 2))
        bg_rect = rect.inflate(40, 20)
        pygame.draw.rect(surface, (15, 15, 25), bg_rect, border_radius=8)
        pygame.draw.rect(surface, C_NEON_BLUE, bg_rect, 2, border_radius=8)
        surface.blit(msg_surface, rect)


# ===========================================================================
#  [11] MENIURI & ECRANE  —  butoane neon, login, meniu, magazin, hărți, personaje
# ===========================================================================
class NeonButton:
    def __init__(self, cx, cy, w, h, text, font, neon_color=C_NEON_BLUE, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        self.text = text; self.font = font
        self.neon_color = neon_color; self.text_color = text_color
        self.hover = False
    def check(self, mp):
        self.hover = self.rect.collidepoint(mp)
    def clicked(self, ev):
        return ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.hover
    def draw(self, surf):
        alpha_fill = 70 if self.hover else 25
        fill_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        fill_surf.fill((*self.neon_color, alpha_fill))
        surf.blit(fill_surf, self.rect.topleft)
        thickness = 3 if self.hover else 1
        pygame.draw.rect(surf, self.neon_color, self.rect, thickness, border_radius=10)
        ts = self.font.render(self.text, True, self.text_color)
        surf.blit(ts, ts.get_rect(center=self.rect.center))


def login_screen(screen, font_title, font_btn, font_sm):
    name = ""
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and name.strip():
                    load_profile(name.strip())
                    return
                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif ev.unicode.isprintable() and len(name) < 15:
                    name += ev.unicode

        screen.fill(C_MENU_BG)
        title = font_title.render("BOMBERMAN  NEON", True, C_NEON_BLUE)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 160)))
        sub = font_sm.render("Introdu numele tău pentru a te loga", True, (150, 150, 180))
        screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 90)))
        box = pygame.Rect(SCREEN_W // 2 - 220, SCREEN_H // 2 - 40, 440, 70)
        pygame.draw.rect(screen, (20, 30, 50), box, border_radius=8)
        pygame.draw.rect(screen, C_NEON_PURP, box, 3, border_radius=8)
        disp_name = name + ("_" if pygame.time.get_ticks() % 1000 < 500 else " ")
        txt = font_btn.render(disp_name if disp_name.strip() else "_", True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=box.center))
        pygame.display.flip()


def draw_profile_widget(screen, font_big, font_sm):
    w, h = 320, 80
    px, py = SCREEN_W - w - 30, 20
    rect = pygame.Rect(px, py, w, h)
    pygame.draw.rect(screen, (15, 22, 35), rect, border_radius=8)
    pygame.draw.rect(screen, C_NEON_BLUE, rect, 2, border_radius=8)
    screen.blit(font_sm.render(f"JUCĂTOR: {PROFILE['name']}", True, C_NEON_BLUE), (px + 16, py + 6))
    screen.blit(font_big.render(f"NIVEL {PROFILE['level']}", True, (255, 255, 255)), (px + 16, py + 26))
    xp_pct = PROFILE["xp"] / max(1, PROFILE["xp_needed"])
    pygame.draw.rect(screen, (40, 40, 60), (px + 16, py + 58, 280, 10))
    pygame.draw.rect(screen, C_NEON_PURP, (px + 16, py + 58, int(280 * xp_pct), 10))
    screen.blit(font_sm.render(f"XP: {PROFILE['xp']}/{PROFILE['xp_needed']}", True, (180, 180, 180)), (px + 16, py + 70))
    screen.blit(font_big.render(f"${PROFILE['money']}", True, (50, 220, 80)), (px + 230, py + 26))


class MainMenu:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.ft, self.fb, self.fs, self.ftt = fonts
        cx = SCREEN_W // 2
        cy_start = SCREEN_H // 2 - 80
        gap = 80
        self.btn_play  = NeonButton(cx, cy_start,       320, 60, "▶  JOACĂ", self.fb)
        self.btn_chars = NeonButton(cx, cy_start + gap,   320, 60, "PERSONAJE", self.fb)
        self.btn_map   = NeonButton(cx, cy_start + gap * 2, 320, 60, "HARTĂ", self.fb)
        self.btn_store = NeonButton(cx, cy_start + gap * 3, 320, 60, "MAGAZIN BOMBE", self.fb, C_NEON_PURP)
        self.btn_quit  = NeonButton(cx, cy_start + gap * 4, 320, 55, "IEȘIRE", self.fb, (220, 50, 50))

    def run(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            mp = pygame.mouse.get_pos()
            btns = [self.btn_play, self.btn_chars, self.btn_map, self.btn_store, self.btn_quit]
            for b in btns:
                b.check(mp)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.btn_play.clicked(ev):  return 'play'
                if self.btn_chars.clicked(ev): return 'chars'
                if self.btn_map.clicked(ev):   return 'map'
                if self.btn_store.clicked(ev): return 'store'
                if self.btn_quit.clicked(ev):
                    save_profile(); pygame.quit(); sys.exit()
            self.screen.fill(C_MENU_BG)
            title = self.ftt.render("BOMBERMAN  NEON", True, C_NEON_BLUE)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 120)))
            sub = self.fs.render(
                "P1: WASD + F (Bombă) + E (Scut)     |     P2: Săgeți + ENTER (Bombă) + RSHIFT (Scut)",
                True, (130, 160, 200))
            self.screen.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 195)))

            bonus_items = [
                (C_BONUS_HP,    "♥ Viată"),
                (C_BONUS_RANGE, "★ Raza bomba"),
                (C_BONUS_BOMBS, "+ Bomba extra"),
                (C_BONUS_SPEED, "▶ Viteza"),
            ]
            bx = SCREEN_W // 2 - 380
            self.screen.blit(self.fs.render("BONUSURI:", True, (180, 180, 180)), (bx, SCREEN_H - 120))
            for bi, (bcol, blbl) in enumerate(bonus_items):
                ix = bx + bi * 200
                pygame.draw.circle(self.screen, bcol, (ix + 10, SCREEN_H - 90), 9)
                self.screen.blit(self.fs.render(blbl, True, C_TEXT), (ix + 24, SCREEN_H - 99))

            for b in btns:
                b.draw(self.screen)
            draw_profile_widget(self.screen, self.fb, self.fs)
            pygame.display.flip()


class StoreScreen:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.ft, self.fb, self.fs, self.ftt = fonts
        cx = SCREEN_W // 2
        self.btn_p1_range = NeonButton(cx - 220, 420, 300, 65, f"P1  Rază +1  (${COST_RANGE})",  self.fb, C_NEON_PURP)
        self.btn_p1_bombs = NeonButton(cx - 220, 510, 300, 65, f"P1  Bombe +1  (${COST_BOMBS})", self.fb, C_NEON_PURP)
        self.btn_p2_range = NeonButton(cx + 220, 420, 300, 65, f"P2  Rază +1  (${COST_RANGE})",  self.fb, C_NEON_PURP)
        self.btn_p2_bombs = NeonButton(cx + 220, 510, 300, 65, f"P2  Bombe +1  (${COST_BOMBS})", self.fb, C_NEON_PURP)
        self.btn_back     = NeonButton(cx, SCREEN_H - 100, 260, 60, "ÎNAPOI", self.fb)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            mp = pygame.mouse.get_pos()
            btns = [self.btn_p1_range, self.btn_p1_bombs,
                    self.btn_p2_range, self.btn_p2_bombs, self.btn_back]
            for b in btns:
                b.check(mp)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.btn_back.clicked(ev):
                    save_profile(); return
                if self.btn_p1_range.clicked(ev) and PROFILE['money'] >= COST_RANGE:
                    PROFILE['money'] -= COST_RANGE; PROFILE['p1_bomb_range'] += 1
                if self.btn_p1_bombs.clicked(ev) and PROFILE['money'] >= COST_BOMBS:
                    PROFILE['money'] -= COST_BOMBS; PROFILE['p1_max_bombs'] += 1
                if self.btn_p2_range.clicked(ev) and PROFILE['money'] >= COST_RANGE:
                    PROFILE['money'] -= COST_RANGE; PROFILE['p2_bomb_range'] += 1
                if self.btn_p2_bombs.clicked(ev) and PROFILE['money'] >= COST_BOMBS:
                    PROFILE['money'] -= COST_BOMBS; PROFILE['p2_max_bombs'] += 1
            self.screen.fill(C_MENU_BG)
            title = self.ftt.render("MAGAZIN BOMBE", True, C_NEON_PURP)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 110)))
            draw_profile_widget(self.screen, self.fb, self.fs)
            cx = SCREEN_W // 2
            p1_stat = self.fb.render(
                f"P1 — Rază: {PROFILE['p1_bomb_range']}   Bombe: {PROFILE['p1_max_bombs']}", True, C_TEXT)
            p2_stat = self.fb.render(
                f"P2 — Rază: {PROFILE['p2_bomb_range']}   Bombe: {PROFILE['p2_max_bombs']}", True, C_TEXT)
            self.screen.blit(p1_stat, p1_stat.get_rect(center=(cx - 220, 340)))
            self.screen.blit(p2_stat, p2_stat.get_rect(center=(cx + 220, 340)))
            for b in btns:
                b.draw(self.screen)
            pygame.display.flip()


class MapSelectScreen:
    def __init__(self, screen, fonts):
        self.screen = screen
        self.ft, self.fb, self.fs, self.ftt = fonts
        self.map_names = list(MAPS.keys())
        self.idx = 0
        self.previews = {}
        for name in self.map_names:
            if MAPS[name] is not None:
                self.previews[name] = render_map_preview(MAPS[name], 600, 420)
            else:
                tmpl = generate_random_map()
                self.previews[name] = render_map_preview(tmpl, 600, 420)
        cx = SCREEN_W // 2
        bottom = SCREEN_H - 80
        self.btn_prev = NeonButton(cx - 300, bottom, 120, 60, "◀", self.fb)
        self.btn_next = NeonButton(cx + 300, bottom, 120, 60, "▶", self.fb)
        self.btn_sel  = NeonButton(cx,       bottom, 240, 60, "SELECTEAZĂ", self.fb, C_NEON_PURP)
        self.btn_back = NeonButton(cx, bottom - 80, 240, 55, "ÎNAPOI", self.fb)

    def run(self, current_map):
        if current_map in self.map_names:
            self.idx = self.map_names.index(current_map)
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            mp = pygame.mouse.get_pos()
            btns = [self.btn_prev, self.btn_next, self.btn_sel, self.btn_back]
            for b in btns:
                b.check(mp)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.btn_back.clicked(ev): return current_map
                if self.btn_sel.clicked(ev):  return self.map_names[self.idx]
                if self.btn_next.clicked(ev): self.idx = (self.idx + 1) % len(self.map_names)
                if self.btn_prev.clicked(ev): self.idx = (self.idx - 1) % len(self.map_names)
            self.screen.fill(C_MENU_BG)
            title = self.ftt.render(f"HARTĂ: {self.map_names[self.idx].upper()}", True, C_NEON_BLUE)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 80)))
            prev = self.previews[self.map_names[self.idx]]
            pw, ph = prev.get_size()
            px = SCREEN_W // 2 - pw // 2
            py = 140
            self.screen.blit(prev, (px, py))
            for b in btns:
                b.draw(self.screen)
            pygame.display.flip()


class CharSelectScreen:
    def __init__(self, screen, fonts, previews):
        self.screen = screen
        self.ft, self.fb, self.fs, self.ftt = fonts
        self.previews = previews
        self.btn_back = NeonButton(SCREEN_W // 2, SCREEN_H - 70, 240, 55, "ÎNAPOI", self.fb)
        self.p1_sel = 0; self.p2_sel = 1

    def run(self, p1_default, p2_default):
        self.p1_sel = p1_default; self.p2_sel = p2_default
        clock = pygame.time.Clock()
        card_size = 110; margin = 30
        n = len(CHARACTERS)
        total_w = n * card_size + (n - 1) * margin

        def make_cards(top_y):
            cards = []
            start_x = SCREEN_W // 2 - total_w // 2
            for i in range(n):
                x = start_x + i * (card_size + margin)
                cards.append(pygame.Rect(x, top_y, card_size, card_size))
            return cards

        p1_top = 200; p2_top = 500
        cards_p1 = make_cards(p1_top)
        cards_p2 = make_cards(p2_top)

        while True:
            clock.tick(60)
            mp = pygame.mouse.get_pos()
            self.btn_back.check(mp)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if self.btn_back.clicked(ev):
                    return self.p1_sel, self.p2_sel
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for i, r in enumerate(cards_p1):
                        if r.collidepoint(mp): self.p1_sel = i
                    for i, r in enumerate(cards_p2):
                        if r.collidepoint(mp): self.p2_sel = i
            self.screen.fill(C_MENU_BG)
            title = self.ftt.render("ALEGE PERSONAJELE", True, C_NEON_BLUE)
            self.screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 90)))
            lbl1 = self.fb.render(f"JUCĂTOR 1  —  {CHARACTERS[self.p1_sel]['name']}", True, CHARACTERS[self.p1_sel]['color'])
            self.screen.blit(lbl1, lbl1.get_rect(center=(SCREEN_W // 2, p1_top - 40)))
            for i, r in enumerate(cards_p1):
                border_col = CHARACTERS[i]['color'] if i == self.p1_sel else (50, 50, 70)
                border_w = 4 if i == self.p1_sel else 1
                pygame.draw.rect(self.screen, (20, 25, 40), r, border_radius=10)
                pygame.draw.rect(self.screen, border_col, r, border_w, border_radius=10)
                scaled = pygame.transform.scale(self.previews[i], (card_size - 10, card_size - 10))
                self.screen.blit(scaled, (r.x + 5, r.y + 5))
            lbl2 = self.fb.render(f"JUCĂTOR 2  —  {CHARACTERS[self.p2_sel]['name']}", True, CHARACTERS[self.p2_sel]['color'])
            self.screen.blit(lbl2, lbl2.get_rect(center=(SCREEN_W // 2, p2_top - 40)))
            for i, r in enumerate(cards_p2):
                border_col = CHARACTERS[i]['color'] if i == self.p2_sel else (50, 50, 70)
                border_w = 4 if i == self.p2_sel else 1
                pygame.draw.rect(self.screen, (20, 25, 40), r, border_radius=10)
                pygame.draw.rect(self.screen, border_col, r, border_w, border_radius=10)
                scaled = pygame.transform.scale(self.previews[i], (card_size - 10, card_size - 10))
                self.screen.blit(scaled, (r.x + 5, r.y + 5))
            self.btn_back.draw(self.screen)
            pygame.display.flip()


# ===========================================================================
#  [12] BUCLA PRINCIPALĂ
# ===========================================================================
def main():
    pygame.init()
    info = pygame.display.Info()
    native_w, native_h = info.current_w, info.current_h

    # [TIPS PREZENTARE]: dacă vrei fereastră mică în loc de FULLSCREEN,
    # șterge ", pygame.FULLSCREEN" și pune o rezoluție fixă, ex. (1280, 720).
    screen = pygame.display.set_mode((native_w, native_h), pygame.FULLSCREEN)
    pygame.display.set_caption("Bomberman Neon Edition")
    clock = pygame.time.Clock()

    global SCREEN_W, SCREEN_H
    SCREEN_W, SCREEN_H = native_w, native_h

    scale = min(native_w / 1920, native_h / 1080)
    font_title = get_font(int(72 * scale), bold=True, name="Trebuchet MS")
    font_btn   = get_font(int(28 * scale), bold=True, name="Trebuchet MS")
    font_big   = get_font(int(22 * scale), bold=True, name="Trebuchet MS")
    font_sm    = get_font(int(17 * scale), bold=False, name="Trebuchet MS")
    fonts = (font_title, font_btn, font_sm, font_title)

    try:
        sheet = pygame.image.load("Bombermannn.png").convert_alpha()
    except Exception:
        print("EROARE: Pune 'Bombermannn.png' în același folder cu scriptul!")
        pygame.quit(); sys.exit()

    login_screen(screen, font_title, font_btn, font_sm)

    all_anims    = [load_char_sprites(sheet, ch["color"]) for ch in CHARACTERS]
    all_previews = [anims['down'][1] for anims in all_anims]

    menu         = MainMenu(screen, fonts)
    char_screen  = CharSelectScreen(screen, fonts, all_previews)
    map_screen   = MapSelectScreen(screen, fonts)
    store_screen = StoreScreen(screen, fonts)

    p1_sel = 0; p2_sel = 1
    current_map = "Clasic"

    grid_w = COLS * TILE
    grid_h = ROWS * TILE
    ox = (native_w - grid_w) // 2
    oy = HUD_HEIGHT + (native_h - HUD_HEIGHT - grid_h) // 2

    # FIX: o singură suprafață de lumină, reutilizată în fiecare cadru (nu mai
    # alocăm 1920x1080 de 60 de ori pe secundă).
    light_map = pygame.Surface((SCREEN_W, SCREEN_H))

    while True:
        action = menu.run()
        if action == 'chars':
            p1_sel, p2_sel = char_screen.run(p1_sel, p2_sel)
            continue
        elif action == 'store':
            store_screen.run()
            continue
        elif action == 'map':
            current_map = map_screen.run(current_map)
            continue

        # --- Pregătirea unei runde noi ---
        if current_map == "Aleatoriu" or MAPS.get(current_map) is None:
            active_template = generate_random_map()
        else:
            active_template = MAPS[current_map]

        grid, p1_pos, p2_pos, bots_pos = build_map(active_template)

        c1 = CHARACTERS[p1_sel]; c2 = CHARACTERS[p2_sel]
        p1 = Player(PROFILE["name"], c1["color"], p1_pos[0], p1_pos[1],
                    (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d, pygame.K_f, pygame.K_e),
                    all_anims[p1_sel], PROFILE['p1_max_bombs'], PROFILE['p1_bomb_range'])
        p2 = Player("Jucator 2", c2["color"], p2_pos[0], p2_pos[1],
                    (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_RSHIFT),
                    all_anims[p2_sel], PROFILE['p2_max_bombs'], PROFILE['p2_bomb_range'])

        bots = [Bot(CHARACTERS[7]["color"], b[0], b[1], all_anims[7]) for b in bots_pos]
        players = [p1, p2] + bots
        num_human_players = 2

        bombs = []
        bonuses = []
        particles = []
        shake_state = [0.0]

        paused = False
        game_over = False
        earnings_saved = False   # FIX: salvăm o singură dată la finalul rundei

        game_time = 0.0
        spiral_coords = get_spiral_coords()
        sd_timer = 0.0
        sudden_death_active = False

        bg = build_bg(grid, ox, oy)
        bg_needs_rebuild = False

        # --- Bucla de joc a rundei ---
        while True:
            dt = min(clock.tick(FPS) / 1000.0, 0.05)

            quit_to_menu = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    save_profile(); pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_SPACE and not game_over:
                        paused = not paused
                    if ev.key in (pygame.K_r, pygame.K_ESCAPE):
                        save_profile()
                        quit_to_menu = True

            if quit_to_menu:
                break

            if not paused and not game_over:
                game_time += dt
                keys = pygame.key.get_pressed()

                for p in players:
                    nb = p.handle_input(keys, grid, bombs, dt)
                    if nb:
                        bombs.append(nb)
                for p in players:
                    p.update(dt)
                    if p.alive and not p.is_bot:
                        p.collect_bonuses(bonuses)

                for b in bonuses:
                    b.update(dt)

                for part in particles:
                    part.update(dt)
                particles = [pt for pt in particles if pt.life > 0]

                to_rm = []
                for b in bombs:
                    if b.update(dt, grid, bombs, players, bonuses, particles, shake_state):
                        to_rm.append(b)
                for b in to_rm:
                    bombs.remove(b)

                sudden_death_active = game_time > SUDDEN_DEATH_START
                if sudden_death_active and spiral_coords:
                    sd_timer -= dt
                    if sd_timer <= 0:
                        sc, sr = spiral_coords.pop(0)
                        if grid[sr][sc] != 'H':
                            grid[sr][sc] = 'H'
                            bg_needs_rebuild = True
                            bonuses[:] = [b for b in bonuses if not (b.col == sc and b.row == sr)]
                            for p in players:
                                if p.alive and p.tile_col() == sc and p.tile_row() == sr:
                                    p.hp = 0; p.alive = False
                                    play_sound(SND_DIE)
                        sd_timer = SUDDEN_DEATH_SPEED

                if bg_needs_rebuild:
                    bg = build_bg(grid, ox, oy)
                    bg_needs_rebuild = False

                humans_alive = sum(1 for p in players[:num_human_players] if p.alive)
                if humans_alive <= 1:
                    game_over = True

            # FIX: salvăm profilul O SINGURĂ DATĂ când se termină runda
            if game_over and not earnings_saved:
                save_profile()
                earnings_saved = True

            # --- Camera cu cutremur (screen shake) ---
            render_ox = ox
            render_oy = oy
            if shake_state[0] > 0:
                shake_state[0] -= dt
                mag = int(shake_state[0] * 20)
                if mag > 0:
                    render_ox += random.randint(-mag, mag)
                    render_oy += random.randint(-mag, mag)

            # --- Desenare de bază ---
            screen.fill((10, 15, 20))
            screen.blit(bg, (render_ox - ox, render_oy - oy))
            draw_dynamic_tiles(screen, grid, render_ox, render_oy)

            for bonus in bonuses:
                bonus.draw(screen, render_ox, render_oy)
            for b in bombs:
                if not b.exploding:
                    b.draw(screen, render_ox, render_oy)
            for p in players:
                p.draw(screen, render_ox, render_oy)
            for b in bombs:
                if b.exploding:
                    b.draw(screen, render_ox, render_oy)
            for part in particles:
                part.draw(screen, render_ox, render_oy)

            for p in players:
                if not p.is_bot:
                    p.draw_bonus_msg(screen, render_ox, render_oy, font_sm)

            # --- Stratul de lumină (iluminare dinamică) ---
            light_map.fill((30, 30, 45))   # culoare ambientală de noapte

            for p in players:
                if p.alive:
                    lx = int(render_ox + p.px + TILE / 2 - L_PLAYER.get_width() / 2)
                    ly = int(render_oy + p.py + TILE / 2 - L_PLAYER.get_height() / 2)
                    light_map.blit(L_PLAYER, (lx, ly), special_flags=pygame.BLEND_RGB_ADD)

            for b in bombs:
                if not b.exploding:
                    lx = int(render_ox + b.col * TILE + TILE / 2 - L_BOMB.get_width() / 2)
                    ly = int(render_oy + b.row * TILE + TILE / 2 - L_BOMB.get_height() / 2)
                    light_map.blit(L_BOMB, (lx, ly), special_flags=pygame.BLEND_RGB_ADD)
                else:
                    for ec, er, tip in b.cells:
                        lx = int(render_ox + ec * TILE + TILE / 2 - L_EXPL.get_width() / 2)
                        ly = int(render_oy + er * TILE + TILE / 2 - L_EXPL.get_height() / 2)
                        light_map.blit(L_EXPL, (lx, ly), special_flags=pygame.BLEND_RGB_ADD)

            screen.blit(light_map, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # --- HUD (desenat peste lumină ca să rămână luminos) ---
            draw_hud(screen, players, font_big, font_sm, font_title,
                     paused, game_over, sudden_death_active)
            pygame.display.flip()


if __name__ == "__main__":
    main()
