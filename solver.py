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
        
        self.nodes = self.extract_nodes()       #Extracts nodes from pairs
        self.solution_path = []                             # To store the final solution path
    
    def extract_nodes(self) -> list[Tuple[int, int]]:
        """Extract all unique nodes from the pairs."""
        if not self.pairs:
            return []
        
        nodes = [self.pairs[0][0]]

        for start, end in self.pairs:
            if nodes[-1] == start:
                nodes.append(end)
            else:
                #Pairs aren't conssecutive
                raise ValueError("Pairs must be in consecutive order.")
        return nodes

    def is_edge_blocked(self, cell1: Tuple[int, int], cell2: Tuple[int, int]) -> bool:
        """Check if the edge between two positions is blocked by a wall."""
        edge = (cell1, cell2)
        return edge in self.walls

    def get_neighbours(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighbouring positions (up, down, left, right) that aren't blocked by walls or already occupied"""
        row, col = pos
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbours = []
        #check each direction
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            neighbour = (new_row, new_col)
            #Checks bounds
            if (0 <= new_row < self.rows and 0 <= new_col < self.cols):
                #Check if edge is blocked by wall
                if not self.is_edge_blocked(pos, neighbour):
                    neighbours.append(neighbour)
        return neighbours
    
    def hamiltonian_path(self, current: Tuple[int, int], 
                visited: set[Tuple[int, int]],
                path: List[Tuple[int, int]],
                next_node_index: int) -> bool:
        """
        ALGORITHM:
        1. Start at node 1
        2. Explores all neighbours through DFS
        3. Must visit nodes 2, 3, ... in order
        4. Must visit all cells on the board
        5. End at final node
        Args:
            current: Current cell position
            visited: Set of cells already visited
            path: Current path taken
            next_node_idx: Index of next required node to visit
        
        Returns:
            True if valid Hamilton path found, False otherwise
        """
        
        #Base Case: Checks if all nodes visited and all cells filled
        if len(visited) == self.total_cells:
            if next_node_index == len(self.nodes):
                self.solution_path = path.copy()
                return True
            return False
        
        #Check if current cell is the next required node
        if (next_node_index < len(self.nodes) and current == self.nodes[next_node_index]):
            next_node_index += 1

        #Explore neighbours using DFS
        for neighbour in self.get_neighbours(current):
            if neighbour in visited:
                continue

            #Can't skip required nodes, if neighbour is a required node that is not next, skip it
            if next_node_index < len(self.nodes):
                future_nodes = self.nodes[next_node_index:]
                if neighbour in future_nodes and neighbour != self.nodes[next_node_index]:
                    continue            #Skip this neighbour (out of order)
            #Explore this path
            visited.add(neighbour)
            path.append(neighbour)

            if self.hamiltonian_path(neighbour, visited, path, next_node_index):
                return True

            #Backtrack
            path.pop()
            visited.remove(neighbour)
        return False
        
    def solve(self) -> bool:
        """
        Main solve function. Returns True if solution found.
        Must fill ALL cells on the board.
        """
        if not self.nodes:
            return False
        
        start_node = self.nodes[0]
        visited = {start_node}
        path = [start_node]
        
        return self.hamiltonian_path(start_node, visited, path, 1)
    
    def print_solution(self):
        """Print the solution paths in a readable format."""
        if not self.solution_path:
            print("No solution found!")
            return
        
        print("Number of Paths:", len(self.solution_path))

        for i, path in enumerate(self.solution_path):
            print("Path", i+1)
            print(path)

    def get_solution_path(self) -> List[Tuple[int, int]]:
       return self.solution_path
    
    def visualize_solution(self):
        """Visualize the solution on a grid showing path order."""

        #Prints out a grid with the solution path marked 1 to N, where 1 is start and N is end
        if not self.solution_path:
            print("No solution to visualize!")
            return
        
        grid = [['.' for _ in range(self.cols)] for _ in range(self.rows)]

        path = self.solution_path
        for step_index, (r, c) in enumerate(path):
            grid[r][c] = str(step_index)  # 0, 1, 2, 3..
        print("Grid Visualization:")
        for row in grid:
            print(' '.join(row))

# Test the solver
if __name__ == "__main__":
    # Simple 3x3 puzzle - guaranteed solvable
    print("=== Test 1: Simple 3x3 grid ===")
    grid_size = (6, 6)
    pairs = [
        ((4, 0), (2, 2)),  # Top-left to bottom-right
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