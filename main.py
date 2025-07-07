# IMPORTS
import pygame
import sys
import random

# Initialize + Global Variables
pygame.init()
pygame.mixer.init()
music_muted = False
elapsed_time = 0
personal_best = 0

# Screen settings
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Sky Runner") # NAME GAME

# Load background
background = pygame.image.load("example.png").convert() # PLACE BACK
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Load music
pygame.mixer.music.load("example.mp3") # PLACE MP3 for SOUNDTRACK HERE
pygame.mixer.music.play(-1)

# Load sprite sheet
def load_sprite_sheet(filename, frame_width, frame_height):
    sheet = pygame.image.load(filename).convert_alpha()
    sheet_width, _ = sheet.get_size()
    frames = []
    for i in range(sheet_width // frame_width):
        frame = sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
        frames.append(frame)
    return frames

# Flash effect
def flash_screen(duration=250):
    flash = pygame.Surface((WIDTH, HEIGHT))
    flash.fill((255, 255, 255))
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < duration:
        SCREEN.blit(flash, (0, 0))
        pygame.display.flip()

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((50, 50, 50))
        self.rect = self.image.get_rect(topleft=(x, y))

# Player with subpixel float motion
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, frames):
        super().__init__()
        self.frames = frames
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.pos = pygame.math.Vector2(x, y)  # Float position
        self.rect.topleft = self.pos
        self.animation_timer = 0
        self.gravity = 0.8
        self.jump_strength = -14
        self.velocity_y = 0
        self.on_ground = False
        self.jump_pressed = False
        self.jump_hold_time = 0
        self.max_jump_hold = 15

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            if not self.jump_pressed and self.on_ground:
                self.velocity_y = self.jump_strength
                self.jump_pressed = True
                self.jump_hold_time = 0
            elif self.jump_pressed:
                if self.jump_hold_time < self.max_jump_hold:
                    self.velocity_y += -0.4
                    self.jump_hold_time += 1
        else:
            self.jump_pressed = False

    def apply_gravity(self, platforms):
        self.velocity_y += self.gravity
        self.pos.y += self.velocity_y
        self.rect.topleft = self.pos
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.velocity_y > 0 and self.rect.bottom <= p.rect.bottom:
                    self.rect.bottom = p.rect.top
                    self.pos.y = self.rect.top
                    self.velocity_y = 0
                    self.on_ground = True

    def animate(self):
        self.animation_timer += 1
        if self.animation_timer >= 10:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.animation_timer = 0

    def update(self, platforms):
        self.handle_input()
        self.apply_gravity(platforms)
        self.animate()

# Generate platforms
def generate_platforms(n, spacing, start_x=250):
    group = pygame.sprite.Group()
    x = start_x
    for _ in range(n):
        w = random.randint(100, 150)
        h = 20
        y = random.randint(HEIGHT - 150, HEIGHT - 100)
        p = Platform(x, y, w, h)
        group.add(p)
        x += w + random.randint(80, 100)
    return group

# Init game
def init_game():
    global player_group, player, platforms, background_x, start_time
    background_x = 0
    player_frames = load_sprite_sheet("example.png", 32, 32) # Sprite PNG - CHANGE FOR CHAR
    player = Player(100, HEIGHT - 150, player_frames)
    player_group = pygame.sprite.Group(player)
    start_platform = Platform(100, HEIGHT - 100, 150, 20)
    platforms = pygame.sprite.Group(start_platform)
    platforms.add(*generate_platforms(10, 100, start_x=250))
    start_time = pygame.time.get_ticks()
    global personal_best

# Start game
init_game()

# Game settings
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
speed_boost_interval = 15 # speed interval
base_scroll_speed = 2
scroll_speed = base_scroll_speed
running = True

# Main loop
while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_m:
                music_muted = not music_muted
                pygame.mixer.music.set_volume(0 if music_muted else 1)

    elapsed = (pygame.time.get_ticks() - start_time) // 1000
    if elapsed > personal_best:
        personal_best = elapsed
    scroll_speed = base_scroll_speed + (elapsed // speed_boost_interval)

    # Scroll background
    background_x -= scroll_speed
    SCREEN.blit(background, (background_x, 0))
    SCREEN.blit(background, (background_x + WIDTH, 0))
    if background_x <= -WIDTH:
        background_x = 0

    # Move platforms
    for platform in platforms:
        platform.rect.x -= scroll_speed

    # Spawn platforms
    for p in list(platforms):
        if p.rect.right < 0:
            platforms.remove(p)
            max_jump_distance = 100
            gap = random.randint(80, max_jump_distance)
            new_x = max(q.rect.right for q in platforms) + gap
            new_y = random.randint(HEIGHT - 150, HEIGHT - 100)
            new_width = random.randint(100, 150)
            new_platform = Platform(new_x, new_y, new_width, 20)
            platforms.add(new_platform)

    # Update & draw
    player_group.update(platforms)
    platforms.draw(SCREEN)
    player_group.draw(SCREEN)

    # Timer
    timer_text = font.render(f"Time: {elapsed}s", True, (255, 255, 255))
    SCREEN.blit(timer_text, (10, 10))

    # Restart on fall
    if player.rect.top > HEIGHT:
        flash_screen()
        init_game()

    best_text = font.render(f"Best: {personal_best}s", True, (255, 255, 0))
    SCREEN.blit(best_text, (WIDTH - best_text.get_width() - 10, 10))
    pygame.display.flip()

pygame.quit()
sys.exit()
