import pyautogui
import time
from typing import List, Tuple, Dict

class ZipAutomation:
    def __init__ (self, cell_positions: Dict[Tuple[int, int], Tuple[int, int]]):
        """
        Initialize automation with cell positions from vision system
        Args:
            cell_positions: Dict mapping (row, col) to (screen_x, screen_y)
        """
        self.cell_positions = cell_positions

        #Safety: Allows user to move mouse to corner to stop
        pyautogui.FAILSAFE = True

        #Allows reasonable speed, can be adjusted
        pyautogui.PAUSE = 0.05 #50ms between actions

    def draw_path(self, path: List[Tuple[int, int]], move_duration: float = 0.1):
        """
        Draw a single path by clicking and dragging through cells

        Args:
            path: List of (row, col) coordinates to draw through
            How long each drag takes (seconds)
        """
        if not path or len(path) < 2:
            print("Path too short to draw.")
            return
        
        print(f"Drawing path with {len(path)} cells.")
        #Get screen position of first cell
        start_cell = path[0]
        start_x, start_y = self.cell_positions[start_cell]
        
        # Move to start position and click down
        pyautogui.moveTo(start_x, start_y, duration=0.2)
        time.sleep(0.1)
        pyautogui.mouseDown(button='left')
        
        # Drag through each subsequent cell
        for i in range(1, len(path)):
            cell = path[i]
            x, y = self.cell_positions[cell]
            if cell not in self.cell_positions:
                pyautogui.mouseUp(button='left')
                raise KeyError(f"Cell {cell} not found in position map")
            x, y = self.cell_positions[cell]
    
            print(f"  -> Visiting cell {cell} at ({x}, {y})")  # ADD THIS LINE
            pyautogui.moveTo(x, y, duration=0.05)
            time.sleep(move_duration)
        
        # Release mouse
        time.sleep(0.1)
        pyautogui.mouseUp(button='left')
        
        print(f"✓ Path drawn: {path[0]} → {path[-1]}")

    def draw_all_paths(self, solution_paths: List[List[Tuple[int, int]]], pause_between_paths: float = 0.5, move_duration: float = 0.1):
        """
        Draw all solution paths with pauses between them.
        
        Args:
            solution_paths: List of paths from solver
            pause_between_paths: Seconds to wait between drawing each path
            move_duration: Speed of drag movements (lower = slower)
        """
        print(f"\n{'='*60}")
        print(f"AUTO-SOLVING ZIP PUZZLE")
        print(f"{'='*60}")
        print(f"Total paths to draw: {len(solution_paths)}")
        print(f"\n SAFETY: Move mouse to corner to abort!")
        print("Starting in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print("\n Starting automation!\n")
        
        for i, path in enumerate(solution_paths):
            print(f"\n--- Path {i+1}/{len(solution_paths)} ---")
            try:
                self.draw_path(path, move_duration=move_duration)
            except pyautogui.FailSafeException:
                print("Automation aborted by failsafe")
                return
            
            if i < len(solution_paths) - 1:
                print(f"Pausing {pause_between_paths}s before next path...")
                time.sleep(pause_between_paths)
        
        print(f"\n{'='*60}")
        print("✓ ALL PATHS DRAWN SUCCESSFULLY!")
        print(f"{'='*60}\n")
    
    def test_single_cell(self, cell: Tuple[int, int]):
        """
        Test automation by clicking on a single cell.
        Useful for debugging position accuracy.
        """
        if cell not in self.cell_positions:
            print(f"Cell {cell} not found in position map")
            return
        
        x, y = self.cell_positions[cell]
        
        print(f"Testing cell {cell} at screen position ({x}, {y})")
        print("Moving mouse in 2 seconds...")
        time.sleep(2)
        
        pyautogui.moveTo(x, y, duration=0.5)
        pyautogui.click()
        print("Click complete")
    
    def preview_path_positions(self, path: List[Tuple[int, int]]):
        """
        Preview where the mouse will move without actually drawing.
        Shows screen coordinates for debugging.
        """
        print("\n Path Preview:")
        print(f"{'Step':<6} {'Cell':<12} {'Screen Position'}")
        print("-" * 40)
        
        for i, cell in enumerate(path):
            if cell in self.cell_positions:
                x, y = self.cell_positions[cell]
                print(f"{i:<6} {str(cell):<12} ({x}, {y})")
            else:
                print(f"{i:<6} {str(cell):<12} NOT FOUND")
