import numpy as np
from shapely.geometry import Polygon, box 

SEED = 42
np.random.seed(SEED)

"""Class for a heightmap."""
class Heightmap:
    def __init__(self, width, depth, resolution=0.5):
        self.width = width
        self.depth = depth
        self.resolution = resolution
        self.grid_x = int(width / resolution)
        self.grid_y = int(depth / resolution)
        self.height = np.zeros((self.grid_x, self.grid_y))
        self.occupancy = np.ones((self.grid_x, self.grid_y), dtype=float)

    def world_to_grid(self, x, y):
        """Convert world coordinates to grid indices."""
        grid_x = int((x + self.width / 2) / self.resolution)
        grid_y = int((y + self.depth / 2) / self.resolution)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x, grid_y):
        """Convert grid indices to world coordinates."""
        x = grid_x * self.resolution - self.width / 2
        y = grid_y * self.resolution - self.depth / 2
        return x, y
    
    def get_height(self, x, y):
        """Get the height at world coordinates (x, y)."""
        grid_x, grid_y = self.world_to_grid(x, y)
        if 0 <= grid_x < self.grid_x and 0 <= grid_y < self.grid_y:
            return self.height[grid_x, grid_y]
        else:
            return None
    
    def update_height(self, position, size, rotation, min_ratio=0.5):
        """Update the heightmap with a block at a given position and size.
        The block can only be placed if the support area ratio is sufficient.
        """
        polygon = self.get_polygon(position, size, rotation)

        min_x, min_y = self.world_to_grid(polygon.bounds[0:2])
        max_x, max_y = self.world_to_grid(polygon.bounds[2:4])

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                grid_min_x, grid_min_y = self.grid_to_world(x, y)
                grid_max_x, grid_max_y = self.grid_to_world(x + 1, y + 1)
                cell = box(grid_min_x, grid_min_y, grid_max_x, grid_max_y)
                
                intersection = cell.interscetion(polygon)

                if not intersection.is_empty:
                    grid_area = self.resolution ** 2
                    inter_area = intersection.area
                    area_ratio = inter_area / grid_area
                    
                    if area_ratio >= min_ratio:
                        self.height[x, y] += position[2]/2
                        self.occupancy[x, y] = area_ratio

        
    def get_polygon(self, position, size, rotation):
        """
        Calculate the support area for a block on the heightmap.
        Only when the ratio is enough, the block can be placed.
        """
        l, w = size[0], size[1]
        angle = rotation[2]

        # Calculate the corners of the block in world coordinates
        corners = [
            (position[0] + l/2 * np.cos(angle) - w/2 * np.sin(angle),
             position[1] + l/2 * np.sin(angle) + w/2 * np.cos(angle)),
            (position[0] + l/2 * np.cos(angle) + w/2 * np.sin(angle),
             position[1] + l/2 * np.sin(angle) - w/2 * np.cos(angle)),
            (position[0] - l/2 * np.cos(angle) + w/2 * np.sin(angle),
             position[1] - l/2 * np.sin(angle) - w/2 * np.cos(angle)),
            (position[0] - l/2 * np.cos(angle) - w/2 * np.sin(angle),
             position[1] - l/2 * np.sin(angle) + w/2 * np.cos(angle))
        ]

        # Create a polygon from the corners
        polygon = Polygon(corners)
        return polygon

    def get_valid_positions(self, size, flag):
        """Get all valid positions on the heightmap."""
        valid_positions = []
        if flag:
            for _ in range(5):
                x = np.random.uniform(-2.5, 2.5)
                y = np.random.uniform(-2.5, 2.5)
                position = (x, y, 1.5)
                valid_positions.append(position)
        else:
            for x in range(self.grid_x):
                for y in range(self.grid_y):
                    if self.occupancy[x, y] >= 0.5 and self.occupancy[x, y] < 1.0:
                        x, y = self.grid_to_world(x, y)
                        position = (x + self.resolution / 2,
                                    y + self.resolution / 2,
                                    self.height[x, y] + size[2] / 2)
                        valid_positions.append(position)
        return valid_positions
