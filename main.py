"""
LinkedIn Zip Auto-Solver
Main integration file that connects vision, solver, and automation
"""
print ("Starting it up")
from vision import ZipVision
from solver import ZipSolver
from automation import ZipAutomation
import time
print("IMports done")
def main():
    print("=" * 70)
    print("LINKEDIN ZIP AUTO-SOLVER")
    print("=" * 70)
    print("\nThis tool will:")
    print("  1. Capture the game board from your screen")
    print("  2. Detect numbered nodes")
    print("  3. Solve the puzzle")
    print("  4. Automatically draw the solution")
    print("\n" + "=" * 70)
    
    # ========================================================================
    # STEP 1: VISION - Capture and analyze the board
    # ========================================================================
    print("\n[STEP 1] BOARD CAPTURE")
    print("-" * 70)
    
    vision = ZipVision()
    
    # Select board area
    vision.select_board_area()
    
    # Capture screenshot
    print("\nCapturing board...")
    img = vision.capture_board()
    print("✓ Board captured")
    
    # Get grid size
    print("\nEnter grid dimensions:")
    rows = int(input("  Rows: "))
    cols = int(input("  Cols: "))
    
    vision.detect_grid_structure(img, expected_size=(rows, cols))
    
    # ========================================================================
    # STEP 2: NUMBER DETECTION
    # ========================================================================
    print("\n[STEP 2] NUMBER DETECTION")
    print("-" * 70)
    
    print("\nType y if you want to try OCR detection first:")
    try_ocr = input("  Try OCR? (y/n): ").lower() == 'y'
    
    if try_ocr:
        print("\nAttempting OCR detection...")
        print("(This requires pytesseract and Tesseract-OCR installed)")
        numbers = vision.detect_numbers_at_cells(img)
        
        if not numbers or len(numbers) < 2:
            print("OCR detection failed or found too few numbers")
            print("\nSwitching to manual input mode")
            print("Enter the number shown in each cell (or press Enter to skip empty cells)")
            
            numbers = {}
            for row in range(rows):
                for col in range(cols):
                    num_input = input(f"  Cell ({row},{col}) number: ").strip()
                    if num_input.isdigit():
                        numbers[(row, col)] = int(num_input)
        else:
            print(f"OCR detected {len(numbers)} numbers successfully")
    else:
        print("\nManual input mode")    
        numbers = {}
        for row in range(rows):
            for col in range(cols):
                num_input = input(f"  Cell ({row},{col}) number: ").strip()
                if num_input.isdigit():
                    numbers[(row, col)] = int(num_input)

    print(f"\nDetected {len(numbers)} numbered cells:")
    for cell, num in sorted(numbers.items(), key=lambda x: x[1]):
        print(f"  {num} at {cell}")
    
    # Create pairs from consecutive numbers
    print("\nCreating pairs from consecutive numbers...")
    pairs = vision.identify_pairs_from_numbers(numbers)
    
    if not pairs:
        print("No valid pairs found! Exiting.")
        return
    
    print(f"Created {len(pairs)} pairs")
    
    # ========================================================================
    # STEP 3: WALL DETECTION (OPTIONAL)
    # ========================================================================
    print("\n[STEP 3] WALL DETECTION")
    print("-" * 70)
    
    # Initialize walls as empty set
    walls = set()
    
    has_walls = input("\nDoes the puzzle have walls? (y/n): ").lower()
    
    if has_walls == 'y':
        # Try automatic wall detection first
        try_auto_walls = input("Try automatic wall detection? (y/n): ").lower()
        
        if try_auto_walls == 'y':
            print("\nAttempting automatic wall detection...")
            detected_walls = vision.detect_walls(img)
            
            if detected_walls:
                print(f"✓ Detected {len(detected_walls)} walls")
                for wall in detected_walls:
                    print(f"  Wall: {wall[0]} ↔ {wall[1]}")
                
                use_detected = input("\nUse these detected walls? (y/n): ").lower()
                if use_detected == 'y':
                    walls = detected_walls
                else:
                    print("Skipping automatic detection, switching to manual input")
            else:
                print("No walls detected automatically")
                print("Switching to manual input")
        
        # Manual wall input if needed
        if not walls:
            print("\nManual wall input mode")
            print("Enter walls as: row1,col1,row2,col2 (adjacent cells)")
            print("Example: 0,0,0,1 means wall between (0,0) and (0,1)")
            print("(Press Enter when done)")
            
            while True:
                wall_input = input("  Wall: ").strip()
                if not wall_input:
                    break
                try:
                    parts = [int(x.strip()) for x in wall_input.split(',')]
                    if len(parts) == 4:
                        wall = ((parts[0], parts[1]), (parts[2], parts[3]))
                        walls.add(wall)
                        print(f"  ✓ Added wall: {wall}")
                    else:
                        print("  ⚠ Invalid format (need 4 numbers)")
                except ValueError:
                    print("  ⚠ Invalid format (need numbers)")
    
    if walls:
        print(f"\nUsing {len(walls)} walls for solving")
    else:
        print("\nNo walls - puzzle has open grid")
    
    # ========================================================================
    # STEP 4: SOLVE THE PUZZLE
    # ========================================================================
    print("\n[STEP 4] SOLVING PUZZLE")
    print("-" * 70)
    
    # Create solver and solve
    print(f"\nSolving {rows}x{cols} grid with {len(pairs)} pairs...")
    solver = ZipSolver((rows, cols), pairs, walls if walls else None)
    
    print("This may take a moment...")
    start_time = time.time()
    solution_found = solver.solve()
    solve_time = time.time() - start_time
    
    if not solution_found:
        print(f"\n✗ No solution found (took {solve_time:.2f}s)")
        print("\nPossible reasons:")
        print("  - Incorrect grid size")
        print("  - Wrong number positions")
        print("  - Missing/incorrect walls")
        print("  - Puzzle is actually unsolvable")
        return
    
    print(f"\n✓ Solution found in {solve_time:.2f}s!")
    solver.print_solution()
    solver.visualize_solution()

    # Visualize detection with solution paths
    visualize = input("\nVisualize detection with solution paths? (y/n): ").lower()
    if visualize == 'y':
        vision.visualize_detection(img, numbers, pairs, solver.solution_path)
    
    # ========================================================================
    # STEP 5: AUTOMATION - Draw the solution
    # ========================================================================
    print("\n[STEP 5] AUTOMATION")
    print("-" * 70)
    
    auto_draw = input("\nAutomatically draw solution? (y/n): ").lower()
    
    if auto_draw != 'y':
        print("Automation skipped. Exiting.")
        return
    
    # Settings
    print("\nAutomation settings:")
    drag_speed = input("  Drag speed (0.01=fast, 0.1=slow) [default: 0.05]: ").strip()
    drag_speed = float(drag_speed) if drag_speed else 0.05
    
    pause_time = input("  Pause at each cell (seconds) [default: 0.1]: ").strip()
    pause_time = float(pause_time) if pause_time else 0.1
    
    # Create automation and draw
    automation = ZipAutomation(vision.cell_positions)
    
    print("\n⚠ IMPORTANT:")
    print("  - Make sure the game is visible and in focus")
    print("  - Do NOT move your mouse during automation")
    print("  - Move mouse to corner to abort (failsafe)")
    
    ready = input("\nReady to start? (yes to proceed): ").lower()
    
    if ready == 'yes':
        automation.draw_path(
            solver.solution_path,
            move_duration=drag_speed,
            pause_at_cell=pause_time
        )
        print("\n🎉 Puzzle solved automatically!")
    else:
        print("Automation cancelled.")
    
    print("\n" + "=" * 70)
    print("Program complete!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()