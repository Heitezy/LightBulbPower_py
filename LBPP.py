import pygame
import sys
import random
from enum import Enum, auto
from typing import List, Tuple, Optional, Set

pygame.init()

GRID_SIZE = (16, 16)
TILE_SIZE = 60
SCREEN_WIDTH = GRID_SIZE[0] * TILE_SIZE
SCREEN_HEIGHT = GRID_SIZE[1] * TILE_SIZE
BACKGROUND_COLOR = (255, 192, 0)
GRID_COLOR = (100, 50, 0)
PIPE_COLOR = (200, 50, 50)
BULB_COLOR = (255, 255, 150)
BULB_OFF_COLOR = (150, 150, 150)
POWER_SOURCE_COLOR = (255, 50, 50)
POWER_INDICATOR_COLOR = (255, 220, 0)

class TileType(Enum):
    EMPTY = auto()
    STRAIGHT = auto()
    ELBOW = auto()
    T_JUNCTION = auto()
    CROSS = auto()
    POWER_SOURCE = auto()
    LIGHT_BULB = auto()

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

ROTATIONS = {
    TileType.STRAIGHT: 2,
    TileType.ELBOW: 4,
    TileType.T_JUNCTION: 4,
    TileType.CROSS: 1,
    TileType.POWER_SOURCE: 4,
    TileType.LIGHT_BULB: 4,
    TileType.EMPTY: 1
}

POWER_SOURCE_CONNECTIONS = [
    [Direction.RIGHT],
    [Direction.DOWN],
    [Direction.LEFT],
    [Direction.UP],
    [Direction.RIGHT, Direction.DOWN],
    [Direction.DOWN, Direction.LEFT],
    [Direction.LEFT, Direction.UP],
    [Direction.UP, Direction.RIGHT],
    [Direction.RIGHT, Direction.DOWN, Direction.LEFT],
    [Direction.UP, Direction.DOWN, Direction.LEFT],
    [Direction.UP, Direction.RIGHT, Direction.LEFT],
    [Direction.UP, Direction.RIGHT, Direction.DOWN],
    [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
]

CONNECTION_MAPS = {
    TileType.EMPTY: [[]],
    TileType.STRAIGHT: [
        [Direction.UP, Direction.DOWN],
        [Direction.LEFT, Direction.RIGHT]
    ],
    TileType.ELBOW: [
        [Direction.DOWN, Direction.RIGHT],
        [Direction.LEFT, Direction.DOWN],
        [Direction.UP, Direction.LEFT],
        [Direction.UP, Direction.RIGHT]
    ],
    TileType.T_JUNCTION: [
        [Direction.LEFT, Direction.RIGHT, Direction.DOWN],
        [Direction.UP, Direction.DOWN, Direction.LEFT],
        [Direction.LEFT, Direction.RIGHT, Direction.UP],
        [Direction.UP, Direction.DOWN, Direction.RIGHT]
    ],
    TileType.CROSS: [
        [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
    ],
    TileType.POWER_SOURCE: [
        [Direction.RIGHT],
        [Direction.DOWN],
        [Direction.LEFT],
        [Direction.UP]
    ],
    TileType.LIGHT_BULB: [
        [Direction.UP],
        [Direction.RIGHT],
        [Direction.DOWN],
        [Direction.LEFT]
    ]
}

class Tile:
    def __init__(self, tile_type: TileType, rotation: int = 0):
        self.tile_type = tile_type
        self.max_rotation = ROTATIONS[tile_type]
        self.rotation = rotation % self.max_rotation
        self.is_powered = tile_type == TileType.POWER_SOURCE
        self.used_in_solution = False
        self.power_connection_pattern = None
        if tile_type == TileType.POWER_SOURCE:
            self.power_connection_pattern = random.randint(0, 12)
    
    def rotate(self):
       if self.max_rotation > 1:
           self.rotation = (self.rotation + 1) % self.max_rotation
           return True
       return False


    def get_connections(self) -> List[Direction]:
       if self.tile_type == TileType.POWER_SOURCE and self.power_connection_pattern is not None:
           base_directions = POWER_SOURCE_CONNECTIONS[self.power_connection_pattern]
           return [Direction((d.value + self.rotation) % 4) for d in base_directions]
       return CONNECTION_MAPS[self.tile_type][self.rotation]


    def is_connected_to(self, direction: Direction) -> bool:
        return direction in self.get_connections()

class PuzzleGame:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[Tile(TileType.EMPTY) for _ in range(width)] for _ in range(height)]
        self.power_sources = []
        self.bulbs = []
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Light Bulb Power Puzzle")
        self.font = pygame.font.SysFont('Arial', 24)
        self.is_solved = False

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_neighbor_position(self, x: int, y: int, direction: Direction) -> Tuple[int, int]:
        if direction == Direction.UP:
            return x, y - 1
        elif direction == Direction.RIGHT:
            return x + 1, y
        elif direction == Direction.DOWN:
            return x, y + 1
        elif direction == Direction.LEFT:
            return x - 1, y
        return x, y

    def get_opposite_direction(self, direction: Direction) -> Direction:
        opposites = {
            Direction.UP: Direction.DOWN,
            Direction.RIGHT: Direction.LEFT,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT
        }
        return opposites[direction]

    def generate_puzzle(self, difficulty: int = 1):
        self.grid = [[Tile(TileType.EMPTY) for _ in range(self.width)] for _ in range(self.height)]
        self.bulbs = []
        self.power_sources = []
        
        num_sources = 1 + difficulty // 2
        num_bulbs = 4 + difficulty * 10
        
        available_positions = [(x, y) for y in range(self.height) for x in range(self.width)]
        random.shuffle(available_positions)
        
        power_source_positions = []
        for i in range(num_sources):
            if not available_positions:
                break
            x, y = available_positions.pop(0)
            
            connections_count = random.randint(1, 4)
            
            if connections_count == 1:
                source_type = random.randint(0, 3)
            elif connections_count == 2:
                source_type = random.randint(4, 7)
            elif connections_count == 3:
                source_type = random.randint(8, 11)
            else:
                source_type = 12
            
            self.grid[y][x] = Tile(TileType.POWER_SOURCE, 0)
            self.grid[y][x].power_connection_pattern = source_type
            
            power_source_positions.append((x, y))
            self.power_sources.append((x, y))
        
        connected = set(power_source_positions)
        frontier = list(power_source_positions)
        
        bulb_positions = []
        while len(bulb_positions) < num_bulbs and frontier and available_positions:
            x, y = random.choice(frontier)
            current_tile = self.grid[y][x]
            
            possible_connections = []
            for direction in current_tile.get_connections():
                nx, ny = self.get_neighbor_position(x, y, direction)
                if self.is_valid_position(nx, ny) and (nx, ny) not in connected:
                    possible_connections.append((direction, nx, ny))
            
            if not possible_connections:
                frontier.remove((x, y))
                continue
                
            direction, nx, ny = random.choice(possible_connections)
            connected.add((nx, ny))
            
            if (nx, ny) in available_positions:
                available_positions.remove((nx, ny))
                
            frontier.append((nx, ny))
                
            opposite_dir = self.get_opposite_direction(direction)
            
            place_bulb = len(bulb_positions) < num_bulbs and random.random() < 0.3
            
            if place_bulb:
                bulb_rotation = 0
                if opposite_dir == Direction.UP:
                    bulb_rotation = 0
                elif opposite_dir == Direction.RIGHT:
                    bulb_rotation = 1
                elif opposite_dir == Direction.DOWN:
                    bulb_rotation = 2
                elif opposite_dir == Direction.LEFT:
                    bulb_rotation = 3
                    
                self.grid[ny][nx] = Tile(TileType.LIGHT_BULB, bulb_rotation)
                bulb_positions.append((nx, ny))
                self.bulbs.append((nx, ny))
            else:
                pipe_types = [TileType.STRAIGHT, TileType.ELBOW, TileType.T_JUNCTION, TileType.CROSS]
                pipe_weights = [4, 4, 2, 1]
                pipe_type = random.choices(pipe_types, weights=pipe_weights)[0]
                
                self.grid[ny][nx] = Tile(pipe_type)
                
                valid_rotations = []
                for rot in range(ROTATIONS[pipe_type]):
                    self.grid[ny][nx].rotation = rot
                    if self.grid[ny][nx].is_connected_to(opposite_dir):
                        valid_rotations.append(rot)
                
                if valid_rotations:
                    self.grid[ny][nx].rotation = random.choice(valid_rotations)
        
        self.finalize_puzzle()
        self.update_power_flow()
        
        for _ in range(3):
            if not all(self.grid[y][x].used_in_solution for x, y in power_source_positions):
                self.finalize_puzzle()
                self.update_power_flow()
        
        self.randomize_rotations()
        self.update_power_flow()

    def finalize_puzzle(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].tile_type not in [TileType.POWER_SOURCE, TileType.LIGHT_BULB, TileType.EMPTY]:
                    self.fix_pipe_connections(x, y)

    def fix_pipe_connections(self, x, y):
        tile = self.grid[y][x]
        neighbors = []
        
        for direction in Direction:
            nx, ny = self.get_neighbor_position(x, y, direction)
            if self.is_valid_position(nx, ny):
                neighbor = self.grid[ny][nx]
                opposite_dir = self.get_opposite_direction(direction)
                if neighbor.tile_type != TileType.EMPTY and neighbor.is_connected_to(opposite_dir):
                    neighbors.append(direction)
        
        if not neighbors:
            tile.tile_type = TileType.EMPTY
            return
            
        num_connections = len(neighbors)
        
        if num_connections == 1:
            tile.tile_type = TileType.LIGHT_BULB
            tile.max_rotation = ROTATIONS[tile.tile_type]
            direction = neighbors[0]
            if direction == Direction.UP:
                tile.rotation = 0
            elif direction == Direction.RIGHT:
                tile.rotation = 1
            elif direction == Direction.DOWN:
                tile.rotation = 2
            elif direction == Direction.LEFT:
                tile.rotation = 3
        elif num_connections == 2:
            tile.tile_type = TileType.STRAIGHT if (
                (Direction.UP in neighbors and Direction.DOWN in neighbors) or
                (Direction.LEFT in neighbors and Direction.RIGHT in neighbors)
            ) else TileType.ELBOW
            tile.max_rotation = ROTATIONS[tile.tile_type]
            
            if tile.tile_type == TileType.STRAIGHT:
                tile.rotation = 0 if Direction.UP in neighbors else 1
            else:
                if Direction.DOWN in neighbors and Direction.RIGHT in neighbors:
                    tile.rotation = 0
                elif Direction.LEFT in neighbors and Direction.DOWN in neighbors:
                    tile.rotation = 1
                elif Direction.UP in neighbors and Direction.LEFT in neighbors:
                    tile.rotation = 2
                elif Direction.UP in neighbors and Direction.RIGHT in neighbors:
                    tile.rotation = 3
        elif num_connections == 3:
            tile.tile_type = TileType.T_JUNCTION
            tile.max_rotation = ROTATIONS[tile.tile_type]
            if Direction.LEFT in neighbors and Direction.RIGHT in neighbors and Direction.DOWN in neighbors:
                tile.rotation = 0
            elif Direction.UP in neighbors and Direction.DOWN in neighbors and Direction.LEFT in neighbors:
                tile.rotation = 1
            elif Direction.LEFT in neighbors and Direction.RIGHT in neighbors and Direction.UP in neighbors:
                tile.rotation = 2
            elif Direction.UP in neighbors and Direction.DOWN in neighbors and Direction.RIGHT in neighbors:
                tile.rotation = 3
        else:
            tile.tile_type = TileType.CROSS
            tile.max_rotation = ROTATIONS[tile.tile_type]
            tile.rotation = 0

    def randomize_rotations(self):
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                if tile.tile_type not in [TileType.EMPTY, TileType.POWER_SOURCE]:
                    tile.max_rotation = ROTATIONS[tile.tile_type]
                    tile.rotation = random.randint(0, tile.max_rotation - 1)

    def update_power_flow(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].tile_type != TileType.POWER_SOURCE:
                    self.grid[y][x].is_powered = False
                self.grid[y][x].used_in_solution = False
        
        visited = set()
        for source_x, source_y in self.power_sources:
            queue = [(source_x, source_y)]
            visited.add((source_x, source_y))
            
            while queue:
                x, y = queue.pop(0)
                current_tile = self.grid[y][x]
                current_tile.is_powered = True
                current_tile.used_in_solution = True
                
                for direction in current_tile.get_connections():
                    nx, ny = self.get_neighbor_position(x, y, direction)
                    
                    if not self.is_valid_position(nx, ny) or (nx, ny) in visited:
                        continue
                    
                    neighbor_tile = self.grid[ny][nx]
                    opposite_dir = self.get_opposite_direction(direction)
                    
                    if neighbor_tile.is_connected_to(opposite_dir):
                        queue.append((nx, ny))
                        visited.add((nx, ny))
        
        all_bulbs_lit = all(self.grid[y][x].is_powered for x, y in self.bulbs)
        all_pipes_used = all(
            self.grid[y][x].used_in_solution or self.grid[y][x].tile_type == TileType.EMPTY
            for y in range(self.height) for x in range(self.width)
        )
        no_leaks = self.check_no_leaks()
        
        self.is_solved = all_bulbs_lit and all_pipes_used and no_leaks
        return self.is_solved

    def check_no_leaks(self) -> bool:
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                if tile.is_powered:
                    for direction in tile.get_connections():
                        nx, ny = self.get_neighbor_position(x, y, direction)
                        if not self.is_valid_position(nx, ny):
                            return False
                        
                        neighbor = self.grid[ny][nx]
                        opposite_dir = self.get_opposite_direction(direction)
                        
                        if neighbor.tile_type == TileType.EMPTY or not neighbor.is_connected_to(opposite_dir):
                            return False
        return True

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        
        for x in range(self.width + 1):
            pygame.draw.line(self.screen, GRID_COLOR, 
                            (x * TILE_SIZE, 0), 
                            (x * TILE_SIZE, SCREEN_HEIGHT), 2)
        
        for y in range(self.height + 1):
            pygame.draw.line(self.screen, GRID_COLOR, 
                            (0, y * TILE_SIZE), 
                            (SCREEN_WIDTH, y * TILE_SIZE), 2)
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                center_x = x * TILE_SIZE + TILE_SIZE // 2
                center_y = y * TILE_SIZE + TILE_SIZE // 2
                
                if tile.tile_type == TileType.EMPTY:
                    continue
                
                color = PIPE_COLOR if tile.is_powered else (100, 20, 20)
                
                if tile.tile_type == TileType.POWER_SOURCE:
                    pygame.draw.rect(self.screen, POWER_SOURCE_COLOR, 
                                    (x * TILE_SIZE + 10, y * TILE_SIZE + 10, 
                                     TILE_SIZE - 20, TILE_SIZE - 20))
                    
                    indicator_size = 10
                    for direction in tile.get_connections():
                        indicator_color = POWER_INDICATOR_COLOR
                        
                        if direction == Direction.UP:
                            pygame.draw.polygon(self.screen, indicator_color, [
                                (center_x, center_y - TILE_SIZE//4),
                                (center_x - indicator_size, center_y - indicator_size),
                                (center_x + indicator_size, center_y - indicator_size)
                            ])
                        elif direction == Direction.RIGHT:
                            pygame.draw.polygon(self.screen, indicator_color, [
                                (center_x + TILE_SIZE//4, center_y),
                                (center_x + indicator_size, center_y - indicator_size),
                                (center_x + indicator_size, center_y + indicator_size)
                            ])
                        elif direction == Direction.DOWN:
                            pygame.draw.polygon(self.screen, indicator_color, [
                                (center_x, center_y + TILE_SIZE//4),
                                (center_x - indicator_size, center_y + indicator_size),
                                (center_x + indicator_size, center_y + indicator_size)
                            ])
                        elif direction == Direction.LEFT:
                            pygame.draw.polygon(self.screen, indicator_color, [
                                (center_x - TILE_SIZE//4, center_y),
                                (center_x - indicator_size, center_y - indicator_size),
                                (center_x - indicator_size, center_y + indicator_size)
                            ])
                
                elif tile.tile_type == TileType.LIGHT_BULB:
                    bulb_color = BULB_COLOR if tile.is_powered else BULB_OFF_COLOR
                    pygame.draw.circle(self.screen, bulb_color, 
                                      (center_x, center_y), TILE_SIZE // 3)
                    
                    connection = tile.get_connections()[0]
                    connection_width = 5
                    conn_length = TILE_SIZE // 2.5
                    conn_color = (200, 100, 50) if tile.is_powered else (100, 50, 25)
                    
                    socket_size = TILE_SIZE // 5
                    socket_color = (80, 80, 80) if tile.is_powered else (60, 60, 60)
                    
                    if connection == Direction.UP:
                        pygame.draw.rect(self.screen, socket_color,
                                        (center_x - socket_size//2, center_y - TILE_SIZE//3 - socket_size, 
                                         socket_size, socket_size))
                        pygame.draw.line(self.screen, conn_color, 
                                        (center_x, center_y - TILE_SIZE//4), 
                                        (center_x, center_y - conn_length), connection_width)
                    elif connection == Direction.RIGHT:
                        pygame.draw.rect(self.screen, socket_color,
                                        (center_x + TILE_SIZE//3, center_y - socket_size//2, 
                                         socket_size, socket_size))
                        pygame.draw.line(self.screen, conn_color, 
                                        (center_x + TILE_SIZE//4, center_y), 
                                        (center_x + conn_length, center_y), connection_width)
                    elif connection == Direction.DOWN:
                        pygame.draw.rect(self.screen, socket_color,
                                        (center_x - socket_size//2, center_y + TILE_SIZE//3, 
                                         socket_size, socket_size))
                        pygame.draw.line(self.screen, conn_color, 
                                        (center_x, center_y + TILE_SIZE//4), 
                                        (center_x, center_y + conn_length), connection_width)
                    elif connection == Direction.LEFT:
                        pygame.draw.rect(self.screen, socket_color,
                                        (center_x - TILE_SIZE//3 - socket_size, center_y - socket_size//2, 
                                         socket_size, socket_size))
                        pygame.draw.line(self.screen, conn_color, 
                                        (center_x - TILE_SIZE//4, center_y), 
                                        (center_x - conn_length, center_y), connection_width)
                    
                    if tile.is_powered:
                        for r in range(5, 15, 5):
                            pygame.draw.circle(self.screen, (255, 255, 200, 100 - r * 6), 
                                              (center_x, center_y), TILE_SIZE // 3 + r, 1)
                
                else:
                    connections = tile.get_connections()
                    
                    for direction in connections:
                        if direction == Direction.UP:
                            pygame.draw.line(self.screen, color, 
                                            (center_x, center_y), 
                                            (center_x, y * TILE_SIZE), 4)
                        elif direction == Direction.RIGHT:
                            pygame.draw.line(self.screen, color, 
                                            (center_x, center_y), 
                                            ((x + 1) * TILE_SIZE, center_y), 4)
                        elif direction == Direction.DOWN:
                            pygame.draw.line(self.screen, color, 
                                            (center_x, center_y), 
                                            (center_x, (y + 1) * TILE_SIZE), 4)
                        elif direction == Direction.LEFT:
                            pygame.draw.line(self.screen, color, 
                                            (center_x, center_y), 
                                            (x * TILE_SIZE, center_y), 4)
                    
                    pygame.draw.circle(self.screen, color, (center_x, center_y), 6)
        
        if self.is_solved:
            win_text = self.font.render("Puzzle Solved!", True, (0, 100, 0))
            text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            pygame.draw.rect(self.screen, (200, 255, 200), 
                           (text_rect.x - 10, text_rect.y - 5, 
                            text_rect.width + 20, text_rect.height + 10))
            self.screen.blit(win_text, text_rect)

    def handle_click(self, pos):
        x, y = pos[0] // TILE_SIZE, pos[1] // TILE_SIZE
        
        if not self.is_valid_position(x, y):
            return
        
        if self.grid[y][x].rotate():
            self.update_power_flow()

def main():
    game = PuzzleGame(GRID_SIZE[0], GRID_SIZE[1])
    game.generate_puzzle(difficulty=1)
    
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.generate_puzzle(difficulty=1)
                elif event.key == pygame.K_1:
                    game.generate_puzzle(difficulty=2)
                elif event.key == pygame.K_2:
                    game.generate_puzzle(difficulty=4)
                elif event.key == pygame.K_3:
                    game.generate_puzzle(difficulty=6)
        
        game.draw()
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()