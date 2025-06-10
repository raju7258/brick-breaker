import pygame
import sys
import random
import os
import math
import json

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
BALL_RADIUS = 10
BRICK_WIDTH = 80
BRICK_HEIGHT = 30
BRICK_GAP = 5
PADDLE_SPEED = 10
BALL_SPEED = 5

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE]

# Power-up types
POWERUP_ENLARGE_PADDLE = 0
POWERUP_EXTRA_BALL = 1
POWERUP_SLOW_BALL = 2
POWERUP_TYPES = 3  # Total number of power-up types

# Create assets directory if it doesn't exist
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# High score file path
HIGH_SCORE_FILE = os.path.join(ASSETS_DIR, "highscore.json")

# Create background image file
def create_background_image():
    bg_path = os.path.join(ASSETS_DIR, "background.jpg")
    if not os.path.exists(bg_path):
        # Create a simple gradient background
        bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            color_value = int(255 * (1 - y / SCREEN_HEIGHT))
            color = (0, 0, color_value)
            pygame.draw.line(bg_surface, color, (0, y), (SCREEN_WIDTH, y))
        pygame.image.save(bg_surface, bg_path)
    return bg_path

# Create sound effect file
def create_bounce_sound():
    # Try mp3 first, then wav as fallback
    sound_path_mp3 = os.path.join(ASSETS_DIR, "bounce.mp3")
    sound_path_wav = os.path.join(ASSETS_DIR, "bounce.wav")
    
    if os.path.exists(sound_path_mp3):
        return sound_path_mp3
    elif os.path.exists(sound_path_wav):
        return sound_path_wav
    else:
        # We can't create a sound file programmatically, so we'll just notify the user
        print(f"Please add a sound file at {sound_path_mp3} or {sound_path_wav} for bounce effects")
        return None

# Level configurations
LEVELS = [
    {"rows": 3, "cols": 8, "ball_speed": 5, "brick_health_max": 1},
    {"rows": 5, "cols": 10, "ball_speed": 6, "brick_health_max": 2},
    {"rows": 6, "cols": 12, "ball_speed": 7, "brick_health_max": 2},
    {"rows": 7, "cols": 14, "ball_speed": 8, "brick_health_max": 3}
]

class PowerUp:
    def __init__(self, x, y, type):
        self.x = x
        self.y = y
        self.type = type
        self.width = 30
        self.height = 30
        self.speed = 3
        self.active = True
        
        # Set color based on power-up type
        if self.type == POWERUP_ENLARGE_PADDLE:
            self.color = PURPLE
        elif self.type == POWERUP_EXTRA_BALL:
            self.color = CYAN
        else:  # POWERUP_SLOW_BALL
            self.color = GREEN
    
    def update(self):
        self.y += self.speed
        # Deactivate if it goes off screen
        if self.y > SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        
        # Draw an icon or letter to indicate power-up type
        font = pygame.font.SysFont(None, 24)
        if self.type == POWERUP_ENLARGE_PADDLE:
            text = font.render("P", True, WHITE)
        elif self.type == POWERUP_EXTRA_BALL:
            text = font.render("B", True, WHITE)
        else:  # POWERUP_SLOW_BALL
            text = font.render("S", True, WHITE)
            
        text_rect = text.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text, text_rect)
    
    def collides_with_paddle(self, paddle_x, paddle_y, paddle_width, paddle_height):
        return (self.x < paddle_x + paddle_width and
                self.x + self.width > paddle_x and
                self.y < paddle_y + paddle_height and
                self.y + self.height > paddle_y)

class Ball:
    def __init__(self, x, y, dx, dy, speed):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.radius = BALL_RADIUS
        self.active = True
    
    def update(self):
        self.x += self.dx
        self.y += self.dy
        
        # Ball collision with walls
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.dx *= -1
        if self.y <= self.radius:
            self.dy *= -1
        
        # Check if ball goes below screen
        if self.y >= SCREEN_HEIGHT:
            self.active = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)

class Brick:
    def __init__(self, x, y, width, height, color, health=1):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.health = health
        self.max_health = health
        self.hit = False
        self.animation_frames = 15
        self.current_frame = 0
        self.particles = []
        self.just_hit = False
        self.hit_animation_frames = 5
        self.hit_animation_current = 0
        self.original_width = width
        self.original_height = height
    
    def create_particles(self):
        # Create particles when brick is destroyed
        num_particles = random.randint(8, 12)
        for _ in range(num_particles):
            # Random position within the brick
            x = random.uniform(self.rect.left, self.rect.right)
            y = random.uniform(self.rect.top, self.rect.bottom)
            
            # Random velocity
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            
            # Random size
            size = random.randint(2, 6)
            
            # Random lifetime
            lifetime = random.randint(10, 20)
            
            # Add particle
            self.particles.append({
                'x': x, 'y': y, 'dx': dx, 'dy': dy, 
                'size': size, 'lifetime': lifetime, 'alpha': 255
            })
    
    def update_particles(self):
        # Update particle positions and lifetimes
        for particle in self.particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['lifetime'] -= 1
            particle['alpha'] = 255 * (particle['lifetime'] / 20)
            
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        if self.hit and self.health <= 0:
            # Create particles on first frame of destruction
            if self.current_frame == 0:
                self.create_particles()
            
            # Update particles
            self.update_particles()
            
            # Draw particles
            for particle in self.particles:
                s = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
                s.fill((self.color[0], self.color[1], self.color[2], particle['alpha']))
                screen.blit(s, (particle['x'], particle['y']))
            
            # Animation when brick is destroyed
            self.current_frame += 1
            
            # Shrinking and fading effect
            if self.current_frame < self.animation_frames:
                scale_factor = 1 - (self.current_frame / self.animation_frames)
                alpha = 255 * scale_factor
                
                # Calculate new dimensions and position for shrinking effect
                new_width = self.original_width * scale_factor
                new_height = self.original_height * scale_factor
                new_x = self.rect.x + (self.original_width - new_width) / 2
                new_y = self.rect.y + (self.original_height - new_height) / 2
                
                # Create a surface with per-pixel alpha
                s = pygame.Surface((new_width, new_height), pygame.SRCALPHA)
                s.fill((self.color[0], self.color[1], self.color[2], alpha))
                screen.blit(s, (new_x, new_y))
            
            return self.current_frame >= self.animation_frames and not self.particles
        else:
            # Hit animation (flash and shake)
            if self.just_hit:
                self.hit_animation_current += 1
                
                # Flash effect
                flash_intensity = 255 * (1 - self.hit_animation_current / self.hit_animation_frames)
                r = min(255, int(self.color[0] + flash_intensity))
                g = min(255, int(self.color[1] + flash_intensity))
                b = min(255, int(self.color[2] + flash_intensity))
                
                # Shake effect
                shake_offset_x = random.randint(-2, 2) if self.hit_animation_current < 3 else 0
                shake_offset_y = random.randint(-2, 2) if self.hit_animation_current < 3 else 0
                
                # Draw the brick with flash and shake
                pygame.draw.rect(screen, (r, g, b), 
                                (self.rect.x + shake_offset_x, 
                                 self.rect.y + shake_offset_y, 
                                 self.rect.width, self.rect.height))
                
                # Reset hit animation when complete
                if self.hit_animation_current >= self.hit_animation_frames:
                    self.just_hit = False
                    self.hit_animation_current = 0
            else:
                # Draw brick with color based on health
                color_factor = self.health / self.max_health
                r = min(255, int(self.color[0] * color_factor + 100))
                g = min(255, int(self.color[1] * color_factor + 100))
                b = min(255, int(self.color[2] * color_factor + 100))
                pygame.draw.rect(screen, (r, g, b), self.rect)
            
            # Draw health indicator if health > 1
            if self.max_health > 1:
                font = pygame.font.SysFont(None, 24)
                text = font.render(str(self.health), True, WHITE)
                text_rect = text.get_rect(center=(self.rect.x + self.rect.width//2, 
                                                 self.rect.y + self.rect.height//2))
                screen.blit(text, text_rect)
            
            return False

# Game class
class BrickBreaker:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Brick Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
        
        # Load background image
        self.bg_path = create_background_image()
        try:
            self.background = pygame.image.load(self.bg_path).convert()
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error:
            self.background = None
            print(f"Could not load background image from {self.bg_path}")
        
        # Load sound effects
        self.sound_path = create_bounce_sound()
        try:
            if self.sound_path:
                self.bounce_sound = pygame.mixer.Sound(self.sound_path)
            else:
                self.bounce_sound = None
        except pygame.error as e:
            self.bounce_sound = None
            print(f"Could not load bounce sound: {e}")
        
        # Load high score
        self.high_score = self.load_high_score()
        
        self.level = 0
        self.paused = False
        self.reset_game()
        
    def load_high_score(self):
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except Exception as e:
            print(f"Error loading high score: {e}")
        return 0
    
    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except Exception as e:
            print(f"Error saving high score: {e}")
        
    def reset_game(self):
        # Paddle setup
        self.paddle_x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
        self.paddle_y = SCREEN_HEIGHT - 50
        self.paddle_width = PADDLE_WIDTH
        
        # Set up balls
        current_level = LEVELS[min(self.level, len(LEVELS) - 1)]
        self.ball_speed = current_level["ball_speed"]
        
        self.balls = [Ball(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 70,
            random.choice([-1, 1]) * self.ball_speed,
            -self.ball_speed,
            self.ball_speed
        )]
        
        # Power-ups setup
        self.power_ups = []
        self.power_up_timers = {
            POWERUP_ENLARGE_PADDLE: 0,
            POWERUP_SLOW_BALL: 0
        }
        
        # Bricks setup
        self.bricks = []
        rows = current_level["rows"]
        cols = current_level["cols"]
        brick_health_max = current_level["brick_health_max"]
        
        for row in range(rows):
            for col in range(cols):
                brick_x = col * (BRICK_WIDTH + BRICK_GAP) + BRICK_GAP + (SCREEN_WIDTH - cols * (BRICK_WIDTH + BRICK_GAP)) // 2
                brick_y = row * (BRICK_HEIGHT + BRICK_GAP) + BRICK_GAP + 50
                
                # Randomly assign health to bricks based on level
                health = random.randint(1, brick_health_max)
                
                self.bricks.append(Brick(
                    brick_x, brick_y, BRICK_WIDTH, BRICK_HEIGHT, 
                    COLORS[row % len(COLORS)], health
                ))
        
        # Game state
        self.score = 0 if self.level == 0 else self.score
        self.game_over = False
        self.game_won = False
        self.level_complete = False
    
    def next_level(self):
        self.level += 1
        if self.level < len(LEVELS):
            self.reset_game()
        else:
            self.game_won = True
            # Check for high score
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Save high score before quitting
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (self.game_over or self.game_won):
                    self.level = 0
                    self.score = 0
                    self.reset_game()
                elif event.key == pygame.K_n and self.level_complete:
                    self.next_level()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
        
        if self.paused:
            return
            
        # Paddle movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.paddle_x > 0:
            self.paddle_x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT] and self.paddle_x < SCREEN_WIDTH - self.paddle_width:
            self.paddle_x += PADDLE_SPEED
    
    def update(self):
        if self.game_over or self.game_won or self.level_complete or self.paused:
            return
        
        # Update power-up timers
        for power_up_type, timer in list(self.power_up_timers.items()):
            if timer > 0:
                self.power_up_timers[power_up_type] -= 1
                
                # Reset effects when timer expires
                if self.power_up_timers[power_up_type] == 0:
                    if power_up_type == POWERUP_ENLARGE_PADDLE:
                        self.paddle_width = PADDLE_WIDTH
                    elif power_up_type == POWERUP_SLOW_BALL:
                        for ball in self.balls:
                            ball.speed = self.ball_speed
                            # Normalize direction but keep speed
                            magnitude = math.sqrt(ball.dx**2 + ball.dy**2)
                            if magnitude > 0:
                                ball.dx = ball.dx / magnitude * ball.speed
                                ball.dy = ball.dy / magnitude * ball.speed
        
        # Update balls
        for ball in self.balls[:]:
            ball.update()
            
            # Ball collision with paddle - improved to handle corner collisions
            paddle_rect = pygame.Rect(self.paddle_x, self.paddle_y, self.paddle_width, PADDLE_HEIGHT)
            
            # Calculate the closest point on the paddle to the ball
            closest_x = max(self.paddle_x, min(ball.x, self.paddle_x + self.paddle_width))
            closest_y = max(self.paddle_y, min(ball.y, self.paddle_y + PADDLE_HEIGHT))
            
            # Calculate distance between ball and closest point
            distance_x = ball.x - closest_x
            distance_y = ball.y - closest_y
            distance = math.sqrt(distance_x * distance_x + distance_y * distance_y)
            
            # Check if the ball is colliding with the paddle
            if distance <= ball.radius:
                if self.bounce_sound:
                    self.bounce_sound.play()
                    
                # Calculate bounce angle based on where the ball hit the paddle
                if closest_x == self.paddle_x or closest_x == self.paddle_x + self.paddle_width:
                    # Hit the side of the paddle
                    ball.dx *= -1
                else:
                    # Hit the top or bottom of the paddle
                    hit_pos = (closest_x - self.paddle_x) / self.paddle_width
                    angle = hit_pos * 2 - 1  # -1 (left) to 1 (right)
                    ball.dx = angle * ball.speed
                    ball.dy = -abs(ball.dy)  # Always bounce up
            
            # Ball collision with bricks
            for brick in self.bricks[:]:
                if brick.hit and brick.health <= 0:
                    continue
                    
                # Calculate the closest point on the brick to the ball
                closest_x = max(brick.rect.left, min(ball.x, brick.rect.right))
                closest_y = max(brick.rect.top, min(ball.y, brick.rect.bottom))
                
                # Calculate distance between ball and closest point
                distance_x = ball.x - closest_x
                distance_y = ball.y - closest_y
                distance = math.sqrt(distance_x * distance_x + distance_y * distance_y)
                
                # Check if the ball is colliding with the brick
                if distance <= ball.radius:
                    brick.health -= 1
                    brick.just_hit = True  # Trigger hit animation
                    
                    if brick.health <= 0:
                        brick.hit = True
                        self.score += 10
                        
                        # Chance to spawn a power-up (20%)
                        if random.random() < 0.2:
                            power_up_type = random.randint(0, POWERUP_TYPES - 1)
                            self.power_ups.append(PowerUp(
                                brick.rect.x + brick.rect.width // 2 - 15,
                                brick.rect.y + brick.rect.height,
                                power_up_type
                            ))
                    else:
                        self.score += 1
                    
                    if self.bounce_sound:
                        self.bounce_sound.play()
                    
                    # Determine bounce direction
                    if closest_x == brick.rect.left or closest_x == brick.rect.right:
                        ball.dx *= -1
                    else:
                        ball.dy *= -1
            
            # Remove inactive balls
            if not ball.active:
                self.balls.remove(ball)
        
        # Update power-ups
        for power_up in self.power_ups[:]:
            power_up.update()
            
            # Check collision with paddle
            if power_up.collides_with_paddle(self.paddle_x, self.paddle_y, self.paddle_width, PADDLE_HEIGHT):
                # Apply power-up effect
                if power_up.type == POWERUP_ENLARGE_PADDLE:
                    self.paddle_width = min(PADDLE_WIDTH * 2, SCREEN_WIDTH - self.paddle_x)
                    self.power_up_timers[POWERUP_ENLARGE_PADDLE] = 600  # 10 seconds at 60 FPS
                
                elif power_up.type == POWERUP_EXTRA_BALL:
                    # Add a new ball
                    if self.balls:
                        # Clone an existing ball but with different direction
                        source_ball = random.choice(self.balls)
                        angle = random.uniform(0, math.pi)
                        new_ball = Ball(
                            source_ball.x,
                            source_ball.y,
                            math.cos(angle) * source_ball.speed,
                            -math.sin(angle) * source_ball.speed,
                            source_ball.speed
                        )
                        self.balls.append(new_ball)
                
                elif power_up.type == POWERUP_SLOW_BALL:
                    # Slow down all balls
                    for ball in self.balls:
                        ball.speed = ball.speed * 0.7
                        # Adjust velocity to match new speed
                        magnitude = math.sqrt(ball.dx**2 + ball.dy**2)
                        if magnitude > 0:
                            ball.dx = ball.dx / magnitude * ball.speed
                            ball.dy = ball.dy / magnitude * ball.speed
                    self.power_up_timers[POWERUP_SLOW_BALL] = 600  # 10 seconds at 60 FPS
                
                # Remove the power-up
                self.power_ups.remove(power_up)
            
            # Remove inactive power-ups
            elif not power_up.active:
                self.power_ups.remove(power_up)
        
        # Remove bricks that have completed their animation
        self.bricks = [brick for brick in self.bricks if not (brick.hit and brick.health <= 0 and brick.current_frame >= brick.animation_frames and not brick.particles)]
        
        # Check if game is over (no balls left)
        if not self.balls:
            self.game_over = True
            # Check for high score
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
        
        # Check if all bricks are broken or being animated
        if not any(not brick.hit or brick.health > 0 for brick in self.bricks):
            if self.level < len(LEVELS) - 1:
                self.level_complete = True
            else:
                self.game_won = True
                # Check for high score
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
    
    def draw(self):
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # Draw paddle
        pygame.draw.rect(self.screen, WHITE, (self.paddle_x, self.paddle_y, self.paddle_width, PADDLE_HEIGHT))
        
        # Draw balls
        for ball in self.balls:
            ball.draw(self.screen)
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen)
        
        # Draw bricks
        for brick in self.bricks:
            brick.draw(self.screen)
        
        # Draw score and level
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        level_text = self.font.render(f"Level: {self.level + 1}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - 120, 10))
        
        # Draw high score
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
        self.screen.blit(high_score_text, (SCREEN_WIDTH // 2 - 100, 10))
        
        # Draw active power-ups
        y_offset = 40
        for power_up_type, timer in self.power_up_timers.items():
            if timer > 0:
                if power_up_type == POWERUP_ENLARGE_PADDLE:
                    power_up_text = self.small_font.render(f"Enlarged Paddle: {timer // 60}s", True, PURPLE)
                elif power_up_type == POWERUP_SLOW_BALL:
                    power_up_text = self.small_font.render(f"Slow Ball: {timer // 60}s", True, GREEN)
                else:
                    continue
                    
                self.screen.blit(power_up_text, (10, y_offset))
                y_offset += 25
        
        # Draw game over or win message
        if self.game_over:
            game_over_text = self.font.render("Game Over! Press R to restart", True, RED)
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 20))
            
            high_score_msg = self.font.render(f"High Score: {self.high_score}", True, YELLOW)
            self.screen.blit(high_score_msg, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20))
        
        if self.game_won:
            win_text = self.font.render("You Win! Press R to restart", True, GREEN)
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 160, SCREEN_HEIGHT // 2 - 20))
            
            high_score_msg = self.font.render(f"High Score: {self.high_score}", True, YELLOW)
            self.screen.blit(high_score_msg, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20))
            
        if self.level_complete:
            level_complete_text = self.font.render("Level Complete! Press N for next level", True, GREEN)
            self.screen.blit(level_complete_text, (SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2))
        
        # Draw pause menu
        if self.paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # Pause text
            pause_text = self.font.render("GAME PAUSED", True, WHITE)
            self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 50))
            
            # Instructions
            instructions = [
                "Press P to resume",
                "Press R to restart",
                "Arrow keys to move paddle"
            ]
            
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + i * 30))
        
        pygame.display.flip()
    
    def run(self):
        while True:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

# Run the game
if __name__ == "__main__":
    game = BrickBreaker()
    game.run()
