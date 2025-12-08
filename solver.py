from typing import List, Tuple, Dict, Optional
from copy import deepcopy
class ZipSolver:
    #Constructor 
    def __init__(self, grid_size: Tuple[int, int], pairs: List[Tuple[Tuple[int, int], Tuple[int, int]]], 
                walls: Optional[set[Tuple[Tuple[int, int], Tuple[int, int]]]] = None):
        """
        Initialize the solver for LinkedIn Zip game.
        
        Args:
            grid_size: (rows, cols) tuple
            pairs: List of ((start_row, start_col), (end_row, end_col)) tuples
            walls: Set of edges that are blocked. Each edge is ((r1,c1), (r2,c2)), order doesn't matter
        """
        self.rows, self.cols = grid_size
        self.pairs = pairs
        self.total_cells = self.rows * self.cols
        self.walls = set()
        
        # Normalize wall edges (make both directions blocked)
        if walls:
            for edge in walls:
                self.walls.add(edge)
                self.walls.add((edge[1], edge[0]))  # Add reverse direction
            
        self.solution_paths = []                                                  # To store the final solution path
    
    def is_edge_blocked(self, cell1: Tuple[int, int], cell2: Tuple[int, int]) -> bool:
        """Check if the edge between two positions is blocked by a wall."""
        edge = (cell1, cell2)
        return edge in self.walls

    def get_neighbours(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighbouring positions (up, down, left, right) that aren't blocked by walsl or already occupied"""
        row, col = pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbours = []
        #check each direction
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            neighbour = (new_row, new_col)
            #Checks bounds
            if 0 <= new_row < self.rows and 0 <= new_col < self.cols:
                #Check if edge is blocked by wall
                if not self.is_edge_blocked(pos, neighbour):
                    neighbours.append(neighbour)
        return neighbours
    
    def dfs_path(self, current: Tuple[int, int], goal: Tuple[int, int],
                occupied_cells: set[Tuple[int, int]], 
                path: List[Tuple[int, int]],
                all_paths: List[List[Tuple[int, int]]],
                max_paths: int = 100) -> None:
        """
        DFS to find all possible paths from current to goal.
        Limits to max_paths to avoid explosion on large grids.
        """
        if len(all_paths) >= max_paths:
            return
        
        if current == goal:
            all_paths.append(path.copy())
            return
        
        for neighbor in self.get_neighbours(current):
            # Skip if cell is occupied (unless it's the goal)
            if neighbor in occupied_cells and neighbor != goal:
                continue
            
            # Skip if already in current path
            if neighbor in path:
                continue
            
            path.append(neighbor)
            # Only add to occupied_cells if it wasn't already there (e.g., not a pre-locked endpoint)
            added = False
            if neighbor not in occupied_cells:
                occupied_cells.add(neighbor)
                added = True
            
            self.dfs_path(neighbor, goal, occupied_cells, path, all_paths, max_paths)
            
            path.pop()
            
            # Only remove if we added it (don't remove pre-locked endpoints)
            if added:
                occupied_cells.remove(neighbor)
        
    def find_all_paths(self, start: Tuple[int, int], goal: Tuple[int, int],
                    occupied_cells: set[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        """Find all possible paths from start to goal avoiding occupied cells."""
        all_paths = []
        self.dfs_path(start, goal, occupied_cells.copy(), [start], all_paths)
        return all_paths
        
    def solve_recursive(self, pair_idx: int,
                    occupied_cells: set[Tuple[int, int]], 
                    paths: List[List[Tuple[int, int]]]) -> bool:
        """
        Recursively solve the puzzle using backtracking.
        IMPORTANT: Must fill ALL cells on the board.
        
        Returns True if solution found, False otherwise.
        """
        # Check if we've connected all pairs
        if pair_idx >= len(self.pairs):
            # SUCCESS: All pairs connected AND all cells filled
            if len(occupied_cells) == self.total_cells:
                self.solution_paths = paths
                return True
            # All pairs connected but not all cells filled - not a valid solution
            return False
        
        # Get current pair to connect
        start, goal = self.pairs[pair_idx]
        
        # Find all possible paths for this pair
        possible_paths = self.find_all_paths(start, goal, occupied_cells)
        
        if not possible_paths:
            # No path possible - dead end
            return False
        
        # Try each possible path (sorted by length to try filling more cells first)
        possible_paths.sort(key=lambda p: len(p), reverse=True)
        
        for path in possible_paths:
            # Mark all cells in path as occupied
            new_occupied = occupied_cells.copy()
            for cell in path:
                new_occupied.add(cell)
            
            # Recursively solve remaining pairs
            new_paths = paths + [path]
            
            if self.solve_recursive(pair_idx + 1, new_occupied, new_paths):
                return True
        
        # None of the paths worked - backtrack
        return False
    
    def solve(self) -> bool:
        """
        Main solve function. Returns True if solution found.
        Must fill ALL cells on the board.
        """
        # Start with start and end points already marked
        occupied_cells = set()
        for start, end in self.pairs:
            occupied_cells.add(start)
            occupied_cells.add(end)
        
        # Start recursive solving
        return self.solve_recursive(0, occupied_cells, [])
    
    def print_solution(self):
        """Print the solution paths in a readable format."""
        if not self.solution_paths:
            print("No solution found!")
            return
        
        total_cells_filled = sum(len(path) for path in self.solution_paths)
        print(f"Solution found with {len(self.solution_paths)} paths:")
        print(f"Total cells filled: {total_cells_filled}/{self.total_cells}")
        
        for i, path in enumerate(self.solution_paths):
            print(f"  Path {i+1}: {path[0]} -> {path[-1]} ({len(path)} cells)")
            
    def visualize_solution(self):
        """Visualize the solution on a grid showing path order."""
        if not self.solution_paths:
            print("No solution to visualize!")
            return

        # Create visual grid
        visual = [['.' for _ in range(self.cols)] for _ in range(self.rows)]

        # For single path, show step numbers
        if len(self.solution_paths) == 1:
            path = self.solution_paths[0]
            for i, pos in enumerate(path):
                # Use numbers 0-9, then letters A-Z
                if i < 10:
                    visual[pos[0]][pos[1]] = str(i)
                else:
                    visual[pos[0]][pos[1]] = chr(ord('A') + i - 10)
        else:
            # Multiple paths - show which path each cell belongs to
            path_symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            for path_idx, path in enumerate(self.solution_paths):
                symbol = path_symbols[path_idx % len(path_symbols)]
                for pos in path:
                    visual[pos[0]][pos[1]] = symbol
    
        # Print grid
        print("\nSolution visualization:")
        if len(self.solution_paths) == 1:
            print("(Numbers show the order of movement: 0→1→2→...)")
        else:
            print("(Letters show which path each cell belongs to)")
    
        for row in visual:
            print(' '.join(row))
    
         # Print detailed path sequences
        print("\nDetailed path sequences:")
        for i, path in enumerate(self.solution_paths):
            print(f"\nPath {i+1}: {len(path)} cells")
            # Show path as sequence of coordinates
            path_str = " → ".join([f"({r},{c})" for r, c in path])
            print(f"  {path_str}")

        # Count empty cells
        empty_count = sum(1 for row in visual for cell in row if cell == '.')
        if empty_count > 0:
            print(f"\n⚠ Warning: {empty_count} cells not filled!")
        else:
            print("\n✓ All cells filled!")

# Test the solver
if __name__ == "__main__":
    # Simple 3x3 puzzle - guaranteed solvable
    print("=== Test 1: Simple 3x3 grid ===")
    grid_size = (3, 3)
    pairs = [
        ((0, 0), (2, 2)),  # Top-left to bottom-right
        ((0, 2), (2, 0)),  # Top-right to bottom-left
    ]
    walls = set()  # No walls
    
    print(f"Grid: {grid_size[0]}x{grid_size[1]} ({grid_size[0]*grid_size[1]} cells total)")
    print(f"Pairs to connect: {len(pairs)}")
    
    solver = ZipSolver(grid_size, pairs, walls)
    
    if solver.solve():
        print("\n✓ Solution found!")
        solver.print_solution()
        solver.visualize_solution()
    else:
        print("\n✗ No solution exists.")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Even simpler 2x3 puzzle
    print("=== Test 2: Simple 2x3 grid ===")
    grid_size = (2, 3)
    pairs = [
        ((0, 0), (1, 2)),  # Top-left to bottom-right
    ]
    walls = set()
    
    print(f"Grid: {grid_size[0]}x{grid_size[1]} ({grid_size[0]*grid_size[1]} cells total)")
    print(f"Pairs to connect: {len(pairs)}")
    
    solver = ZipSolver(grid_size, pairs, walls)
    
    if solver.solve():
        print("\n✓ Solution found!")
        solver.print_solution()
        solver.visualize_solution()
    else:
        print("\n✗ No solution exists.")