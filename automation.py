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
        pyautogui.PAUSE = 0.01 #10ms between actions

    def draw_path(self, path: List[Tuple[int, int]], move_duration: float = 0.05, pause_at_cell: float = 0.1):
        """
        Draw the complete solution path by clicking and dragging through all cells.

        Args:
            path: List of (row, col) coordinates representing the Hamiltonian path
            move_duration: How long each drag movement takes (seconds)
            pause_at_cell: How long to pause at each cell for game to register (seconds)
        """
        if not path or len(path) < 2:
            print("Path too short to draw (need at least 2 cells).")
            return
        
        print(f"\n{'='*60}")
        print(f"DRAWING SOLUTION PATH")
        print(f"{'='*60}")
        print(f"Path length: {len(path)} cells")
        print(f"SAFETY: Move mouse to corner to abort!")
        print("\nStarting in 3 seconds...")
        
        for i in range(3, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print("\n🖱️  Starting automation!\n")
        
        # Get screen position of first cell
        start_cell = path[0]
        if start_cell not in self.cell_positions:
            raise KeyError(f"Start cell {start_cell} not found in position map")
        
        start_x, start_y = self.cell_positions[start_cell]
        
        # Move to start position and click down
        print(f"Starting at {start_cell} ({start_x}, {start_y})")
        pyautogui.moveTo(start_x, start_y, duration=0.2)
        time.sleep(0.1)
        pyautogui.mouseDown(button='left')
        
        try:
            # Drag through each subsequent cell
            for i in range(1, len(path)):
                cell = path[i]
                
                if cell not in self.cell_positions:
                    pyautogui.mouseUp(button='left')
                    raise KeyError(f"Cell {cell} not found in position map")
                
                x, y = self.cell_positions[cell]
                
                print(f"  [{i}/{len(path)-1}] → {cell} at ({x}, {y})")
                pyautogui.moveTo(x, y, duration=move_duration)
                time.sleep(pause_at_cell)  # Pause so game registers the cell
            
            # Release mouse
            time.sleep(0.05)
            pyautogui.mouseUp(button='left')
            
            print(f"\n✓ Path drawn successfully: {path[0]} → {path[-1]}")
            print(f"{'='*60}\n")
            
        except pyautogui.FailSafeException:
            print("\n⚠️  Automation aborted by failsafe (mouse moved to corner)")
            pyautogui.mouseUp(button='left')
            return

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
