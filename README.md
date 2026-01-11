# LinkedIn Zip Auto-Solver

What started as a friendly race between my friends and me to see who could crack each LinkedIn Zip puzzle the fastest quickly turned into a 3AM “there has to be a way to guarantee first place” experiment.
That experiment became a fully automated solver powered by computer vision, Hamiltonian path algorithms, and  mouse automation. It detects the puzzle, computes the optimal path, and completes it instantly, no human reflexes required!

## Features
- **Hamiltonian Path Solver**: Finds optimal path that traverses every node exactly once in the required order
- **Automation**: Draws solution automatically with the mouse controlled by the program
- **Vision System**: Detects board, cells, numbers (OCR Detection), and walls 

## Requirements
```
pyautogui
opencv
pillow
numpy
Optional (for ocr)
pytesseract
```

## Project Structure
```
FastestZipFinder/
├── main.py             # Main integration script
├── vision.py           # Board capture and detection
├── solver.py           # Hamiltonian path solver
├── automation.py       # Mouse control and drawing
├── README.md
```

## How It Works
### 1. Vision System (`vision.py`)
- Captures a screenshot of a game board
- Detects grid structure by dividing board into cells
- Uses OCR to read numbers inside of cells
- Detects walls by identifying thick black lines

### 2. Solver ('solver.py')
Uses a **Hamiltonian Path Algorithm**
- Hamiltonian path visits each cell exactly once
- Essentially DFS with following constraints:
    - Must visit number nodes in order (1->2->3->...)
    - Must visit ALL cells
    - Cannot cross walls
    - Must end at final node

**Algorithm**: Depth First Search with backtracking
- Start at node 1
- Visit each neighbour recursively
- Enforce node ordering (ie can't skip nodes)
- Backtrack if dead-end
- Time complexity: O(n!) in worst case, pruning helps

### 3. Automation ('automation.py')
- Moves mouse to each cell position
- Holds left mouse button down
- Drags through the entire solution path
- Slight pause at each cell to ensure game registers it

## Usage
### Basic Usage
```powershell
py main.py
```

### Step-by-Step
1. **Board Selection**
    - Position mouse at top-left corner
    - Press Enter
    - Position mouse at bottom right corner
    - Press Enter

2. **Grid Size**
    - Enter number of rows
    - Enter number of columns

3. **Number Detection**
    - OCR attempts automatic detection
    - Falls back to manual input if needed
        - Enter number for each cell (or enter to skip)

4. **Wall Detection**
    - System automatically detects walls
    - Fall back to manual input
        - Wall is defined as two adjacent cells

5. **Solving**
    - Algorithm finds Hamiltonian path
    - Shows solution visualization

6. **Automation**
    - Confirm you're ready
    - Mouse automatically draws solution
    - Move mouse to corner to abort (failsafe)

## Configuration

### Automation Speed
When prompted adjust:
- **Drag speed**: `0.05` = fast, `0.2` = slow (how long to pause at each cell)

## Algorithm Details

### Hamiltonian Path constraints
```python
def find_hamiltonian_path(current, visited, path, next,_node_idx)
    # Base case: visited all cells?
    if len(visited) == total_cells:
        if current == last_node:
            return True  # Solution found!
    
    # Try each neighbor
    for neighbor in get_neighbors(current):
        if neighbor not in visited:
            # Constraint: can't skip nodes
            if neighbor is future_node and not next_node:
                continue
            
            # Explore
            visited.add(neighbor)
            if find_hamilton_path(neighbor, ...):
                return True
            visited.remove(neighbor)  # Backtrack
    
    return False
```

### Why Hamiltonian Path?
**Old Approach**: Find seperate paths for each pair, and combine them
- Complex back tracking
- Multiple path conflicts
- Hard to ensure all cells filled

**New Approach**: One path through all cells
- Simpler algorithm
- Naturally fills all cells
- Fewer Conflicts

## Trouble Shooting

### OCR Not Working
- Install Tesseract-OCR and pytesseract
- Use manual input fallback
- Ensure numbers are clearly visible

### Improving OCR
1. Ensure game is clearly visible
2. Use full screen or large window
3. Good contrast between numbers and background
4. Install Tesseract-OCR for better results

### Automation Not Accurate
- Slow down drag speed (increase to 0.2-0.3)
- Be more precise when selecting board corners
- Ensure game window doesn't move

### Solver Too Slow
- Reduce grid size (smaller puzzles)
- Increase `max_paths` limit in solver
- Use simpler puzzle first to test

### Mouse Lands Off-Center
- Reselect board area more carefully
- Make sure game window is stationary
- Check if cell size calculation is accurate

## Safety Features

- **Failsafe**: Move mouse to screen corner to abort
- **Preview mode**: Visualize detection before solving
- **Manual input**: Always available if OCR fails
- **Validation**: Checks solution before drawing

## Known Limitations

- Grid must be rectangular (no irregular shapes)
- Walls must be thick black lines
- Requires Python 3.9+

## Future Improvements

- [ ] Automatic grid size detection
- [ ] Faster solving with better pruning
- [ ] Improved OCR detection
- [ ] Allows for removed cells
- [ ] Look into bit masking to improve time complexity
## License

Educational project - use at your own risk. Not affiliated with LinkedIn.

## Credits

Built using:
- OpenCV for computer vision
- PyAutoGUI for automation
- Tesseract for OCR
- NumPy for numerical operations

## Contributing

Improvements welcome! Focus areas:
- Better OCR accuracy
- Faster solving algorithm
- More robust wall detection
- UI improvements
