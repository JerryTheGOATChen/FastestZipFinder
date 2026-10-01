# LinkedIn Zip Auto-Solver

What started as a friendly race between my friends and me to see who could crack each LinkedIn Zip puzzle the fastest quickly turned into a 3AM “there has to be a way to guarantee first place” experiment.
That experiment became a fully automated solver powered by computer vision, Hamiltonian path algorithms, and keyboard/mouse automation. It spots the puzzle on screen, computes the path, and plays it instantly, no human reflexes required!

## Features
- **Vision System**: Finds the board on screen and reads the grid size, numbers (OCR) and walls, nothing to type in
- **Hamiltonian Path Solver**: Finds the path that covers every cell exactly once and hits the numbers in order
- **Automation**: Plays the solution into the game with the arrow keys (or by dragging the mouse)

## Setup
Requires Python 3.10+.

```powershell
py -m pip install -r requirements.txt
```

Number reading uses [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki), which has to be installed separately. It is picked up from `PATH` or from `C:\Program Files\Tesseract-OCR`. Without it the program asks you to type the numbers in.

## Usage
1. Open [linkedin.com/games/zip](https://www.linkedin.com/games/zip/) in your browser, stop at the "Start game" screen
2. Run the solver in a terminal that does not cover the board:
    ```powershell
    py main.py
    ```
3. Click "Start game"

The solver watches the screen, and as soon as the board shows up it reads it, solves it, clicks the `1` and steers the path with the arrow keys. Don't touch the mouse or keyboard until it is done (about a second). Slam the mouse into the top-left corner of the screen to abort.

### Options
| Option | What it does |
| --- | --- |
| `--dry-run` | Find and solve the board, print the solution, leave the mouse and keyboard alone |
| `--mouse` | Drag the path with the mouse instead of using the arrow keys |
| `--step SECONDS` | Pause between moves (default `0.02`). Raise it if the game misses moves |
| `--timeout SECONDS` | How long to wait for a board to show up (default `60`) |
| `--image FILE` | Read the board from a screenshot file instead of the screen (never plays) |
| `--debug` | Save a picture of what was detected to `zip_debug.png` |

## Project Structure
```
FastestZipFinder/
├── main.py             # Command line, ties the three parts together
├── vision.py           # Screen capture, board/number/wall detection
├── solver.py           # Hamiltonian path solver
├── automation.py       # Keyboard and mouse control
├── tests/              # Unit tests and real board screenshots
├── requirements.txt
├── README.md
```

## How It Works
### 1. Vision System (`vision.py`)
- Screenshots the desktop
- Keeps only long straight dark lines, then looks for a square group of evenly spaced ones: that is the board, and the number of lines gives the grid size
- A cell with a black disc in the middle holds a number, which is cut out and read with OCR. The numbers must come out as 1..N with no repeats, otherwise the unclear ones are asked for
- An edge between two cells with a thick black bar on it is a wall

### 2. Solver (`solver.py`)
A **Hamiltonian path** visits each cell exactly once. The solver is a depth first search with backtracking from node 1 under these constraints:
- Must visit number nodes in order (1->2->3->...)
- Must visit ALL cells
- Cannot cross walls
- Must end at the final node

Plain DFS is O(n!) in the worst case, so each step first checks that the unvisited cells can still be covered, and backtracks straight away if not:
- **Colouring**: on a checkerboard every step changes colour, so the counts of unvisited cells of each colour have to match
- **Reachability**: the next number must be reachable without stepping on a later one
- **Links**: every unvisited cell still needs two free neighbours (one for the final node), and cells with no neighbours to spare force their neighbours' choices
- **Cut cells**: a cell that is the only way into a pocket of the board can be crossed once, so the pocket behind it has to hold the end of the path

The visited set is a bitmask, so these checks are a handful of integer operations. A search that guesses wrong early can still get lost, so each attempt has a step budget and restarts from the other end of the path with a different tie-break when it runs out. 6x6 and 7x7 boards solve in a few milliseconds.

### 3. Automation (`automation.py`)
- Clicks the `1` cell to focus the board, then presses one arrow key per step of the path
- With `--mouse`: holds the left button down and drags through every cell instead

## Tests
```powershell
py -m unittest
```
The vision tests run against real screenshots of the game in `tests/fixtures`.

## Troubleshooting

### "No fresh Zip board found"
- The whole board has to be visible on screen, not covered by the terminal
- LinkedIn has to be in its light theme
- The board must not have a path on it yet, press Reset in the game
- Run `py main.py --dry-run --debug` and look at `zip_debug.png`

### Numbers are misread
- Zoom the browser in, bigger digits read better
- Check that Tesseract-OCR is installed

### The game misses moves
- Raise the pause, e.g. `--step 0.05`
- Make sure nothing else grabs the keyboard focus while it plays

## Known Limitations
- Light theme only
- The board has to be a square grid with no path drawn yet
- Mixed-DPI multi monitor setups may put the click in the wrong place, keep the game on the primary monitor

## License

Educational project - use at your own risk. Not affiliated with LinkedIn.

## Credits

Built using:
- OpenCV for computer vision
- PyAutoGUI for automation
- Tesseract for OCR
- NumPy for numerical operations
