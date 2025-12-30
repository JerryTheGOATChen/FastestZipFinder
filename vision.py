import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import time
from typing import Tuple, List, Dict, Set, Optional

class ZipVision:
    def __init__(self):
        self.board_area: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
        self.cell_size: Optional[Tuple[float, float]] = None
        self.grid_size: Optional[Tuple[int, int]] = None  # (rows, cols)
        self.cell_positions: Dict[Tuple[int, int], Tuple[int, int]] = {}  # Maps (row, col) -> (screen_x, screen_y)
        
    def select_board_area(self):
        """
        Interactive: User clicks two corners to define the game board area.
        """
        print("=" * 60)
        print("BOARD AREA SELECTION")
        print("=" * 60)
        print("\nInstructions:")
        print("1. Position your mouse at the TOP-LEFT corner of the game board")
        print("2. Press ENTER when ready...")
        input()
        
        print("3. Click the TOP-LEFT corner now!")
        time.sleep(1)
        top_left = pyautogui.position()
        print(f"   ✓ Top-left captured: {top_left}")
        
        print("\n4. Now position your mouse at the BOTTOM-RIGHT corner")
        print("5. Press ENTER when ready...")
        input()
        
        print("6. Click the BOTTOM-RIGHT corner now!")
        time.sleep(1)
        bottom_right = pyautogui.position()
        print(f"   ✓ Bottom-right captured: {bottom_right}")
        
        # Calculate board area
        x = top_left[0]
        y = top_left[1]
        width = bottom_right[0] - top_left[0]
        height = bottom_right[1] - top_left[1]
        
        self.board_area = (x, y, width, height)
        print(f"\n✓ Board area set: {width}x{height} pixels at ({x}, {y})")
        print("=" * 60)
        
    def capture_board(self) -> np.ndarray:
        """
        Capture screenshot of the board area.
        Returns OpenCV image (BGR format).
        """
        if not self.board_area:
            raise ValueError("Board area not set! Call select_board_area() first.")
        
        x, y, width, height = self.board_area
        
        # Capture screenshot
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        
        # Convert PIL image to OpenCV format (BGR)
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        return img
    
    def detect_grid_structure(self, img: np.ndarray, expected_size: Optional[Tuple[int, int]] = None):
        """
        Detect grid structure by finding lines or using expected size.
        
        Args:
            img: OpenCV image of the board
            expected_size: (rows, cols) if you know the grid size
        """
        if not self.board_area:
            raise ValueError("Board area not set! Call select_board_area() first.")
        
        height, width = img.shape[:2]
        
        if expected_size:
            # If we know the grid size, calculate cell positions directly
            rows, cols = expected_size
            self.grid_size = expected_size
            
            cell_width = width / cols
            cell_height = height / rows
            self.cell_size = (cell_width, cell_height)
            
            # Calculate center position of each cell
            for row in range(rows):
                for col in range(cols):
                    center_x = int(self.board_area[0] + (col + 0.5) * cell_width)
                    center_y = int(self.board_area[1] + (row + 0.5) * cell_height)
                    self.cell_positions[(row, col)] = (center_x, center_y)
            
            print(f"✓ Grid structure detected: {rows}x{cols}")
            print(f"✓ Cell size: {cell_width:.1f}x{cell_height:.1f} pixels")
            print(f"✓ Mapped {len(self.cell_positions)} cell positions")
        else:
            # TODO: Implement automatic grid detection using edge detection
            print("⚠ Automatic grid detection not implemented yet.")
            print("   Please use expected_size parameter.")
    
    def detect_numbers_at_cells(self, img: np.ndarray) -> Dict[Tuple[int, int], int]:
        """
        Use OCR to detect numbers at each cell.
        Returns dict mapping (row, col) -> number.
        """
        if not self.cell_positions:
            raise ValueError("Grid structure not detected! Call detect_grid_structure() first.")
    
        if not self.board_area:
            raise ValueError("Board area not set! Call select_board_area() first.")
        
        if not self.cell_size:
            raise ValueError("Cell size not detected! Call detect_grid_structure() first.")
        # Try to import pytesseract for OCR
        try:
            import pytesseract
        except ImportError:
            print("⚠ pytesseract not installed. Install with: pip install pytesseract")
            print("   Also needs Tesseract-OCR installed on system")
            return {}
        
        numbers = {}
        
        for cell, (screen_x, screen_y) in self.cell_positions.items():
            # Convert screen coordinates to image coordinates
            img_x = screen_x - self.board_area[0]
            img_y = screen_y - self.board_area[1]
            
            # Extract small region around cell center
            cell_w, cell_h = self.cell_size
            x1 = max(0, int(img_x - cell_w * 0.3))
            y1 = max(0, int(img_y - cell_h * 0.3))
            x2 = min(img.shape[1], int(img_x + cell_w * 0.3))
            y2 = min(img.shape[0], int(img_y + cell_h * 0.3))
            
            cell_img = img[y1:y2, x1:x2]
            
            # Convert to grayscale and threshold
            gray = cv2.cvtColor(cell_img, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
            
            # OCR to detect number
            config = '--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(thresh, config=config).strip()
            
            if text.isdigit():
                numbers[cell] = int(text)
        
        return numbers
    
    def identify_pairs_from_numbers(self, numbers: Dict[Tuple[int, int], int]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Create pairs from numbered nodes: n → n+1
        
        Args:
            numbers: Dict of (row, col) -> number
        
        Returns:
            List of pairs: [((r1, c1), (r2, c2)), ...] where numbers[r1,c1] + 1 == numbers[r2,c2]
        """
        # Invert the dict to find positions by number
        pos_by_number = {num: pos for pos, num in numbers.items()}
        
        pairs = []
        sorted_numbers = sorted(pos_by_number.keys())
        
        print(f"Found nodes: {sorted_numbers}")
        
        # Create consecutive pairs: 1→2, 2→3, 3→4, etc.
        for i in range(len(sorted_numbers) - 1):
            current_num = sorted_numbers[i]
            next_num = sorted_numbers[i + 1]
            
            # Check if consecutive
            if next_num == current_num + 1:
                start_pos = pos_by_number[current_num]
                end_pos = pos_by_number[next_num]
                pairs.append((start_pos, end_pos))
                print(f"✓ Pair found: {current_num}→{next_num} at {start_pos} → {end_pos}")
            else:
                print(f"⚠ Gap detected: {current_num} to {next_num} (not consecutive)")
        
        return pairs
    
    def visualize_detection(self, img: np.ndarray, numbers: Dict[Tuple[int, int], int], 
                       pairs: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                       solution_path: Optional[List[Tuple[int, int]]] = None):
        """
        Draw the detected grid, numbers, pairs, and optionally the solution paths.
        
        Args:
            img: The board image
            numbers: Dict of cell -> number
            pairs: List of pairs to connect
            solution_path: solution path to visualize
        """
        if not self.board_area:
            raise ValueError("Board area not set!")

        if not self.grid_size:
            raise ValueError("Grid size not detected!")
        
        if not self.cell_positions:
            raise ValueError("Cell positions not detected!")
        
        vis_img = img.copy()
        
        # Draw grid
        if self.cell_size:
            cell_w, cell_h = self.cell_size
            rows, cols = self.grid_size
            
            for i in range(rows + 1):
                y = int(i * cell_h)
                cv2.line(vis_img, (0, y), (vis_img.shape[1], y), (128, 128, 128), 1)
            
            for i in range(cols + 1):
                x = int(i * cell_w)
                cv2.line(vis_img, (x, 0), (x, vis_img.shape[0]), (128, 128, 128), 1)
        
        # Draw solution paths if provided
        if solution_path:
            color = (255, 0, 0) # Blue for solution path
            
            for i in range(len(solution_path) - 1):
                start_cell = solution_path[i]
                end_cell = solution_path[i + 1]

                start_pos = self.cell_positions[start_cell]
                end_pos = self.cell_positions[end_cell]
                
                # Convert to image coordinates
                start_x = start_pos[0] - self.board_area[0]
                start_y = start_pos[1] - self.board_area[1]
                end_x = end_pos[0] - self.board_area[0]
                end_y = end_pos[1] - self.board_area[1]
                    
                # Draw thick line for path
                cv2.line(vis_img, (start_x, start_y), (end_x, end_y), color, 3)
                
            # Mark start and end
            start_pos = self.cell_positions[solution_path[0]]
            end_pos = self.cell_positions[solution_path[-1]]
        
        # Draw numbers at cells
        for cell, number in numbers.items():
            pos = self.cell_positions[cell]
            x = pos[0] - self.board_area[0]
            y = pos[1] - self.board_area[1]
            
            cv2.putText(vis_img, str(number), (x-10, y+10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        
        # Show image
        cv2.imshow('Detection Visualization', vis_img)
        print("\nPress any key in the image window to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()