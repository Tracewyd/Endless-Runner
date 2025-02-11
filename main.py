import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# ---------------------------
# Global Constants & Settings
# ---------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# These values define our perspective "window."
HORIZON = 150          # Y coordinate of the horizon line (top of the road)
GROUND_Y = 550         # Y coordinate where the ground (road) meets the bottom

# Colors (RGB)
SKY_BLUE = (135, 206, 235)
GRAY = (50, 50, 50)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Add to Global Constants section
PLAYER_COLORS = {
    'BLUE': (0, 0, 255),
    'RED': (255, 0, 0),
    'GREEN': (0, 255, 0),
    'YELLOW': (255, 255, 0),
    'PURPLE': (128, 0, 128)
}

# Add to Global Constants section
DIFFICULTIES = {
    'EASY': {'speed': 0.005, 'interval': 1500},
    'MEDIUM': {'speed': 0.008, 'interval': 1000},
    'HARD': {'speed': 0.012, 'interval': 800}
}

# Update ROAD_SPEED to match obstacle speeds
ROAD_SPEED = DIFFICULTIES['MEDIUM']['speed']  # Use medium difficulty as base speed

# ---------------------------
# Projection Function
# ---------------------------
def project(world_x, world_y, jump_offset=0):
    """
    Given a world coordinate (world_x, world_y) where:
      - world_y = 0 corresponds to the horizon
      - world_y = 1 corresponds to ground level,
    this function computes the screen (pixel) position and a scale factor.
    """
    # Our scale factor increases linearly from 0.5 at the horizon to 1.0 at the ground
    scale = 0.5 + 0.5 * world_y
    screen_x = SCREEN_WIDTH / 2 + world_x * scale
    # Adjust the y-coordinate calculation to allow spawning above the horizon
    screen_y = HORIZON + (GROUND_Y - HORIZON) * world_y - jump_offset
    return int(screen_x), int(screen_y), scale

# ---------------------------
# Player Class
# ---------------------------
class Player:
    def __init__(self, color=BLUE, difficulty='MEDIUM'):
        self.world_y = 1
        self.height = 0  # Current height above ground
        self.width = 50
        self.base_height = 80
        self.color = color
        
        # Jump parameters based on difficulty
        self.difficulty = difficulty
        if difficulty == 'EASY':
            self.jump_gravity = 0.2    # Slower fall
            self.jump_strength = 20    # Higher jump
        elif difficulty == 'MEDIUM':
            self.jump_gravity = 0.3
            self.jump_strength = 15
        else:  # HARD
            self.jump_gravity = 0.4    # Faster fall
            self.jump_strength = 10    # Lower jump
            
        self.is_jumping = False
        self.jump_velocity = 0
        
        # Lane management
        self.LANES = [-150, 0, 150]  # Left, Center, Right lanes only
        self.current_lane = 1  # Start in center lane (index 1 now)
        self.world_x = self.LANES[self.current_lane]
        self.target_x = self.world_x
        self.transition_speed = 0.15
        self.last_key_state = {'a': False, 'd': False}

    def move(self, keys):
        # Lane-based movement with key press detection
        if keys[pygame.K_a] and not self.last_key_state['a'] and self.current_lane > 0:  # Move left
            self.current_lane -= 1
            self.target_x = self.LANES[self.current_lane]
        if keys[pygame.K_d] and not self.last_key_state['d'] and self.current_lane < len(self.LANES) - 1:  # Move right
            self.current_lane += 1
            self.target_x = self.LANES[self.current_lane]
            
        # Update previous key states
        self.last_key_state['a'] = keys[pygame.K_a]
        self.last_key_state['d'] = keys[pygame.K_d]
            
        # Smooth transition to target lane
        diff = self.target_x - self.world_x
        self.world_x += diff * self.transition_speed

    def update(self):
        if self.is_jumping:
            self.height += self.jump_velocity
            self.jump_velocity -= self.jump_gravity
            
            if self.height <= 0:
                self.height = 0
                self.is_jumping = False
                self.jump_velocity = 0

    def draw(self, surface):
        screen_x, screen_y, scale = project(self.world_x, self.world_y, self.height)
        draw_width = int(self.width * scale)
        draw_height = int(self.base_height * scale)
        
        # Draw shadow (only when jumping)
        if self.height > 0:
            # Shadow stays on the ground (screen_y is the ground level)
            # Scale shadow size based on height (larger when higher, smaller when lower)
            shadow_scale = 1.0 - (self.height / 100)  # Adjust 100 for desired scaling range
            shadow_radius = int(draw_width * 0.4 * shadow_scale)  # Base size * scaling factor
            shadow_rect = pygame.Rect(
                screen_x - shadow_radius,  # Center horizontally
                screen_y - shadow_radius // 2,  # Position on the ground
                shadow_radius * 2,
                shadow_radius
            )
            pygame.draw.ellipse(surface, (200, 200, 200), shadow_rect)  # Light gray shadow
        
        # Draw player
        player_rect = pygame.Rect(
            screen_x - draw_width // 2,
            screen_y - draw_height,
            draw_width,
            draw_height
        )
        pygame.draw.rect(surface, self.color, player_rect)
        
        # Return hitbox for collision detection
        hitbox_rect = pygame.Rect(
            player_rect.x,
            player_rect.y,
            player_rect.width,
            player_rect.height
        )
        return hitbox_rect, self.height

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.jump_velocity = self.jump_strength

# ---------------------------
# Obstacle Class
# ---------------------------
class Obstacle:
    def __init__(self, difficulty='MEDIUM'):
        lane_options = [-150, 0, 150]
        self.world_x = random.choice(lane_options)
        self.world_y = -0.2  # Start above the screen (negative value)
        self.height = random.choice([0, 50])
        self.base_width = 50
        self.base_height = 50
        self.color = RED
        self.speed = DIFFICULTIES[difficulty]['speed']
        self.hitbox_height = 10  # Height of the collision hitbox

    def update(self):
        self.world_y += self.speed

    def draw(self, surface):
        screen_x, screen_y, scale = project(self.world_x, self.world_y)
        draw_width = int(self.base_width * scale)
        draw_height = int(self.base_height * scale)
        
        # Draw obstacle
        obstacle_rect = pygame.Rect(
            screen_x - draw_width // 2,
            screen_y - draw_height,
            draw_width,
            draw_height
        )
        pygame.draw.rect(surface, self.color, obstacle_rect)
        
        # Return hitbox for collision detection (only the top 10% of the obstacle)
        hitbox_height = int(draw_height * 0.1)  # Top 10% of the obstacle
        hitbox_rect = pygame.Rect(
            obstacle_rect.x,
            obstacle_rect.y,
            obstacle_rect.width,
            hitbox_height
        )
        return hitbox_rect, self.height

    def is_off_screen(self):
        # If the obstacle goes past the ground (with a little margin), it is removed
        return self.world_y > 1.1

# ---------------------------
# Draw Background Function
# ---------------------------
def draw_background(surface, road_offset=0):
    # Draw the sky
    surface.fill(SKY_BLUE)
    
    # Draw the road as a trapezoid to simulate perspective
    # Extend the road polygon to fill more space
    left_bottom = (SCREEN_WIDTH * 0.1, SCREEN_HEIGHT)  # Extend bottom to screen edge
    right_bottom = (SCREEN_WIDTH * 0.9, SCREEN_HEIGHT)  # Extend bottom to screen edge
    left_top = (SCREEN_WIDTH * 0.4, 0)  # Extend top to screen edge
    right_top = (SCREEN_WIDTH * 0.6, 0)  # Extend top to screen edge
    road_polygon = [left_bottom, right_bottom, right_top, left_top]
    pygame.draw.polygon(surface, GRAY, road_polygon)
    
    # Draw lane dividers with perspective
    lane_color = WHITE
    num_dashes = 40  # Increase number of dashes for smoother animation
    
    # Calculate lane positions with perspective
    for i in range(num_dashes):
        # Add road_offset to create movement
        perspective = (i / num_dashes + road_offset) % 1.0
        
        # Calculate start and end points of current dash
        y1 = 0 + (SCREEN_HEIGHT - 0) * perspective
        y2 = 0 + (SCREEN_HEIGHT - 0) * (perspective + 0.5/num_dashes)
        
        # Outer lines (original road boundaries)
        left_outer_x1 = SCREEN_WIDTH * (0.4 + (0.1 - 0.4) * perspective)
        left_outer_x2 = SCREEN_WIDTH * (0.4 + (0.1 - 0.4) * (perspective + 0.5/num_dashes))
        
        right_outer_x1 = SCREEN_WIDTH * (0.6 + (0.9 - 0.6) * perspective)
        right_outer_x2 = SCREEN_WIDTH * (0.6 + (0.9 - 0.6) * (perspective + 0.5/num_dashes))
        
        # Calculate the total width at each point
        bottom_width = right_outer_x1 - left_outer_x1
        
        # Inner lines at 1/3 and 2/3 of the width
        left_inner_x1 = left_outer_x1 + bottom_width / 3
        left_inner_x2 = left_outer_x2 + bottom_width / 3
        
        right_inner_x1 = right_outer_x1 - bottom_width / 3
        right_inner_x2 = right_outer_x2 - bottom_width / 3
        
        # Draw the dashed lines
        if i % 2 == 0:  # Only draw every other segment for dashed effect (1:1 ratio)
            pygame.draw.line(surface, lane_color, (left_outer_x1, y1), (left_outer_x2, y2), 2)
            pygame.draw.line(surface, lane_color, (left_inner_x1, y1), (left_inner_x2, y2), 2)
            pygame.draw.line(surface, lane_color, (right_inner_x1, y1), (right_inner_x2, y2), 2)
            pygame.draw.line(surface, lane_color, (right_outer_x1, y1), (right_outer_x2, y2), 2)

# ---------------------------
# Collision Detection
# ---------------------------
def check_collision(player_rect, player_height, obs_rect, obs_height):
    """
    Check for collision with top of obstacles and make player invulnerable while jumping
    """
    # If player is jumping at all, they are invulnerable
    if player_height > 0:
        return False
        
    # Use the obstacle's hitbox for collision
    return player_rect.colliderect(obs_rect)

# ---------------------------
# Main Game Loop
# ---------------------------
def draw_menu(surface, font, selected_option, current_color, high_score, difficulty):
    """Draw the main menu with play, color selection, and difficulty options"""
    # Dark background
    surface.fill((30, 30, 30))  # Dark gray background
    
    # Title with gradient effect
    title_text = font.render("Pseudo 3D Endless Runner", True, (200, 200, 200))  # Updated title
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH/2, 150))
    surface.blit(title_text, title_rect)
    
    # Draw a subtle line under the title
    pygame.draw.line(surface, (100, 100, 100), (SCREEN_WIDTH/2 - 200, 180), (SCREEN_WIDTH/2 + 200, 180), 2)
    
    # Options with hover effect
    options = [
        ("Play", (SCREEN_WIDTH/2, 250)),
        (f"Color: {current_color}", (SCREEN_WIDTH/2, 300)),
        (f"Difficulty: {difficulty}", (SCREEN_WIDTH/2, 350))
    ]
    
    option_rects = []
    for i, (text, pos) in enumerate(options):
        # Background rectangle for each option
        bg_rect = pygame.Rect(SCREEN_WIDTH/2 - 150, pos[1] - 20, 300, 40)
        pygame.draw.rect(surface, (50, 50, 50) if selected_option != i else (80, 80, 80), bg_rect, border_radius=10)
        
        # Text with highlight effect
        color = (200, 200, 200) if selected_option != i else (255, 255, 255)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=pos)
        surface.blit(text_surface, text_rect)
        option_rects.append(bg_rect)  # Use the background rect for click detection
    
    # High Score with modern look
    if high_score > 0:
        high_score_text = font.render(f"High Score: {high_score // 1000}", True, (150, 150, 255))  # Light blue
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH/2, 400))
        surface.blit(high_score_text, high_score_rect)

    
    return option_rects

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pseudo‑3D Endless Runner")
    clock = pygame.time.Clock()
    
    # Game state management: "menu", "playing", "game_over"
    state = "menu"
    
    # Initialize player and obstacles (they will be reset each game)
    player = Player()
    obstacles = []
    obstacle_timer = 0
    obstacle_interval = 1000  # in milliseconds between obstacle spawns
    score = 0
    font = pygame.font.SysFont("Arial", 30)

    # Add new variables
    high_score = 0
    selected_option = 0  # 0 for Play, 1 for Color, 2 for Difficulty
    current_color_name = 'BLUE'
    current_color = PLAYER_COLORS[current_color_name]
    current_difficulty = 'HARD'
    option_rects = []  # Store clickable areas
    road_offset = 0.0  # Add this line
    
    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if state == "menu":
                # Handle mouse events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(mouse_pos):
                            if i == 0:  # Play
                                state = "playing"
                                player = Player(current_color, current_difficulty)
                                obstacles = []
                                score = 0
                                obstacle_timer = 0
                                obstacle_interval = DIFFICULTIES[current_difficulty]['interval']
                            elif i == 1:  # Change Color
                                color_names = list(PLAYER_COLORS.keys())
                                current_index = color_names.index(current_color_name)
                                current_color_name = color_names[(current_index + 1) % len(color_names)]
                                current_color = PLAYER_COLORS[current_color_name]
                            elif i == 2:  # Change Difficulty
                                diff_levels = list(DIFFICULTIES.keys())
                                current_index = diff_levels.index(current_difficulty)
                                current_difficulty = diff_levels[(current_index + 1) % len(diff_levels)]
                
                # Handle keyboard events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_option = (selected_option - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        selected_option = (selected_option + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        if selected_option == 0:  # Play
                            state = "playing"
                            player = Player(current_color, current_difficulty)
                            obstacles = []
                            score = 0
                            obstacle_timer = 0
                            obstacle_interval = DIFFICULTIES[current_difficulty]['interval']
                        elif selected_option == 1:  # Change Color
                            color_names = list(PLAYER_COLORS.keys())
                            current_index = color_names.index(current_color_name)
                            current_color_name = color_names[(current_index + 1) % len(color_names)]
                            current_color = PLAYER_COLORS[current_color_name]
                        elif selected_option == 2:  # Change Difficulty
                            diff_levels = list(DIFFICULTIES.keys())
                            current_index = diff_levels.index(current_difficulty)
                            current_difficulty = diff_levels[(current_index + 1) % len(diff_levels)]
            
            elif state == "playing":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.jump()
            elif state == "game_over":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    state = "menu"

        keys = pygame.key.get_pressed()
        if state == "playing":
            # Update player and obstacles
            player.move(keys)
            player.update()
            
            # Update road offset using current difficulty speed
            road_offset += DIFFICULTIES[current_difficulty]['speed']
            if road_offset >= 1.0:
                road_offset -= 1.0
                
            # Update obstacles with the same speed
            for obs in obstacles[:]:
                obs.speed = DIFFICULTIES[current_difficulty]['speed']  # Sync obstacle speed
                obs.update()
                if obs.is_off_screen():
                    obstacles.remove(obs)
            
            # Spawn obstacles with random grouping
            obstacle_timer += dt
            if obstacle_timer > obstacle_interval:
                obstacle_timer = 0
                
                # Adjust weights based on difficulty
                if current_difficulty == 'EASY':
                    weights = [0.8, 0.2, 0.0]  # Mostly single obstacles
                elif current_difficulty == 'MEDIUM':
                    weights = [0.6, 0.3, 0.1]  # Some doubles, rare triples
                else:  # HARD
                    weights = [0.4, 0.4, 0.2]  # More doubles and triples
                    
                num_obstacles = random.choices([1, 2, 3], weights=weights)[0]
                for _ in range(num_obstacles):
                    obstacles.append(Obstacle(current_difficulty))
                
                # Randomize interval slightly for more variety
                obstacle_interval = DIFFICULTIES[current_difficulty]['interval'] * random.uniform(0.8, 1.2)
                
            # Draw everything
            draw_background(screen, road_offset)
            
            # Draw difficulty in the top left
            difficulty_text = font.render(f"Difficulty: {current_difficulty}", True, (200, 200, 200))
            screen.blit(difficulty_text, (10, 10))  # Positioned in the top left
            
            # Draw obstacles and player
            for obs in obstacles:
                obs_rect, obs_height = obs.draw(screen)
                if check_collision(player_rect, player_height, obs_rect, obs_height):
                    state = "game_over"
                    break
            player_rect, player_height = player.draw(screen)
            
            # Draw score
            score_text = font.render(f"Score: {score // 1000}", True, BLACK)
            high_score_text = font.render(f"Best: {high_score // 1000}", True, BLACK)
            screen.blit(score_text, (SCREEN_WIDTH - 200, 10))
            screen.blit(high_score_text, (SCREEN_WIDTH - 200, 40))
            
            # Draw score
            score += dt

        # Update high score when game ends
        if state == "game_over":
            high_score = max(high_score, score)

        # Clear the screen before drawing
        screen.fill(SKY_BLUE)
        
        if state == "menu":
            option_rects = draw_menu(screen, font, selected_option, current_color_name, high_score, current_difficulty)
        elif state == "playing":
            # Draw background with road animation
            draw_background(screen, road_offset)
            # Draw obstacles and player
            for obs in obstacles:
                obs_rect, obs_height = obs.draw(screen)
                if check_collision(player_rect, player_height, obs_rect, obs_height):
                    state = "game_over"
                    break
            player_rect, player_height = player.draw(screen)
            # Draw score
            score_text = font.render(f"Score: {score // 1000}", True, BLACK)
            high_score_text = font.render(f"Best: {high_score // 1000}", True, BLACK)
            screen.blit(score_text, (SCREEN_WIDTH - 200, 10))
            screen.blit(high_score_text, (SCREEN_WIDTH - 200, 40))
        elif state == "game_over":
            # Draw background without animation
            draw_background(screen)
            # Draw game over text
            game_over_text = font.render("Game Over! Press ENTER for Menu", True, RED)
            score_text = font.render(f"Score: {score // 1000}", True, BLACK)
            high_score_text = font.render(f"Best: {high_score // 1000}", True, BLACK)
            screen.blit(game_over_text, (SCREEN_WIDTH/2 - game_over_text.get_width()/2, SCREEN_HEIGHT/2))
            screen.blit(score_text, (SCREEN_WIDTH/2 - score_text.get_width()/2, SCREEN_HEIGHT/2 + 40))
            screen.blit(high_score_text, (SCREEN_WIDTH/2 - high_score_text.get_width()/2, SCREEN_HEIGHT/2 + 80))
            
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    main()

