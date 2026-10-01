"""Finds a LinkedIn Zip board in a screenshot and reads its numbers and walls.

The board (light theme) is a square of thin grey grid lines on a near-white
background. Numbers are white digits on black discs in the middle of a cell,
walls are thick black bars sitting on the line between two cells.
"""
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import cv2
import numpy as np
from PIL import ImageGrab

Cell = Tuple[int, int]
Wall = Tuple[Cell, Cell]

LINE_MAX_GRAY = 215     # grid lines, walls and discs are all darker than this
INK_MAX_GRAY = 90       # walls and number discs are near-black
MIN_LINE_LENGTH = 80    # px, shortest run of dark pixels that counts as a grid line
MIN_GRID, MAX_GRID = 3, 15

TESSERACT_DEFAULT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@dataclass
class Board:
    xs: List[float]                     # x of each vertical grid line, left to right (image px)
    ys: List[float]                     # y of each horizontal grid line, top to bottom
    numbered: List[Cell] = field(default_factory=list)      # cells holding a number disc
    walls: Set[Wall] = field(default_factory=set)
    numbers: Dict[Cell, int] = field(default_factory=dict)  # filled in by read_numbers()

    @property
    def rows(self) -> int:
        return len(self.ys) - 1

    @property
    def cols(self) -> int:
        return len(self.xs) - 1

    @property
    def cell_size(self) -> float:
        return (self.xs[-1] - self.xs[0]) / self.cols

    def center(self, cell: Cell) -> Tuple[int, int]:
        """Pixel at the middle of a cell, in image coordinates."""
        row, col = cell
        return (round((self.xs[col] + self.xs[col + 1]) / 2),
                round((self.ys[row] + self.ys[row + 1]) / 2))

    def same_puzzle(self, other: Optional["Board"]) -> bool:
        """True if another capture shows this exact board in the same place."""
        return (other is not None
                and (self.rows, self.cols) == (other.rows, other.cols)
                and self.numbered == other.numbered and self.walls == other.walls
                and abs(self.xs[0] - other.xs[0]) < 2 and abs(self.ys[0] - other.ys[0]) < 2)


def capture_screen() -> Tuple[np.ndarray, Tuple[int, int], float]:
    """
    Screenshot the desktop.

    Returns (image in BGR, origin, scale). A pixel (x, y) of the image sits at
    mouse position (origin + (x, y) / scale).
    """
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()   # so pixels and mouse coordinates agree
        shot = ImageGrab.grab(all_screens=True)
        # The virtual desktop starts left of / above (0, 0) when a monitor sits there
        origin = (ctypes.windll.user32.GetSystemMetrics(76), ctypes.windll.user32.GetSystemMetrics(77))
        scale = 1.0
    else:
        import pyautogui
        shot = ImageGrab.grab()
        origin = (0, 0)
        scale = shot.width / pyautogui.size().width     # 2.0 on Retina displays
    return cv2.cvtColor(np.array(shot.convert("RGB")), cv2.COLOR_RGB2BGR), origin, scale


def find_board(img: np.ndarray) -> Optional[Board]:
    """
    Locate the Zip board and work out its grid, numbered cells and walls.
    Returns None if no untouched board is visible.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    dark = (gray < LINE_MAX_GRAY).astype(np.uint8)

    # Keep only long straight runs of dark pixels, text and icons drop out
    horizontal = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((1, MIN_LINE_LENGTH), np.uint8))
    vertical = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((MIN_LINE_LENGTH, 1), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(horizontal | vertical, connectivity=8)

    best = None
    for x, y, w, h, _ in stats[1:count]:
        if min(w, h) < MIN_GRID * 30 or abs(w - h) > 0.05 * max(w, h):
            continue    # the board is always square
        xs = _grid_lines(vertical[y:y + h, x:x + w].mean(axis=0), x)
        ys = _grid_lines(horizontal[y:y + h, x:x + w].mean(axis=1), y)
        if xs and ys and len(xs) == len(ys) and (best is None or w > best[0]):
            best = (w, xs, ys)
    if best is None:
        return None

    board = Board(xs=best[1], ys=best[2])
    board.numbered = _find_numbered_cells(gray, board)
    board.walls = _find_walls(gray, board)
    return board


def _grid_lines(profile: np.ndarray, offset: int) -> Optional[List[float]]:
    """
    Turn a projection of the line mask into evenly spaced grid line positions.

    profile[i] is the share of row/column i covered by line pixels. Returns
    None when the peaks do not look like a regular grid.
    """
    hits = np.flatnonzero(profile > 0.5)
    if len(hits) == 0:
        return None
    # Neighbouring hits belong to the same (possibly thick) line
    groups = np.split(hits, np.flatnonzero(np.diff(hits) > 2) + 1)
    lines = [float(group.mean()) for group in groups]
    size = len(lines) - 1
    if not MIN_GRID <= size <= MAX_GRID:
        return None
    gaps = np.diff(lines)
    if np.abs(gaps - np.median(gaps)).max() > 0.15 * np.median(gaps):
        return None
    return [offset + float(v) for v in np.linspace(lines[0], lines[-1], size + 1)]


def _find_numbered_cells(gray: np.ndarray, board: Board) -> List[Cell]:
    """Cells whose middle is covered by a black number disc."""
    reach = max(2, int(board.cell_size * 0.15))
    numbered = []
    for row in range(board.rows):
        for col in range(board.cols):
            cx, cy = board.center((row, col))
            patch = gray[cy - reach:cy + reach + 1, cx - reach:cx + reach + 1]
            if (patch < INK_MAX_GRAY).mean() > 0.35:
                numbered.append((row, col))
    return numbered


def _find_walls(gray: np.ndarray, board: Board) -> Set[Wall]:
    """Pairs of adjacent cells with a thick black bar on the line between them."""
    along = max(2, int(board.cell_size * 0.2))      # how far to look along the edge
    across = max(1, int(board.cell_size * 0.05))    # how far to look either side of it, wider than a grid line

    def is_wall(x: float, y: float, vertical_edge: bool) -> bool:
        x, y = round(x), round(y)
        dx, dy = (across, along) if vertical_edge else (along, across)
        patch = gray[y - dy:y + dy + 1, x - dx:x + dx + 1]
        return (patch < INK_MAX_GRAY).mean() > 0.6

    walls = set()
    for row in range(board.rows):
        for col in range(board.cols):
            cx, cy = board.center((row, col))
            if col + 1 < board.cols and is_wall(board.xs[col + 1], cy, True):
                walls.add(((row, col), (row, col + 1)))
            if row + 1 < board.rows and is_wall(cx, board.ys[row + 1], False):
                walls.add(((row, col), (row + 1, col)))
    return walls


def _tesseract():
    """The pytesseract module ready for use, or None if OCR is not installed."""
    try:
        import pytesseract
    except ImportError:
        return None
    if not shutil.which("tesseract"):
        if not os.path.exists(TESSERACT_DEFAULT):
            return None
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_DEFAULT
    return pytesseract


def warm_up_ocr():
    """Run tesseract once on nothing, its first launch is much slower than the rest."""
    pytesseract = _tesseract()
    if pytesseract:
        try:
            pytesseract.image_to_string(np.full((32, 32), 255, np.uint8), config="--psm 7")
        except (pytesseract.TesseractError, OSError):
            pass    # read_numbers() will report the problem if it is a real one


def read_numbers(img: np.ndarray, board: Board) -> List[Cell]:
    """
    OCR the number in every numbered cell into board.numbers.

    Returns the cells that could not be read reliably (empty when every
    number 1..N was found exactly once).
    """
    pytesseract = _tesseract()
    if pytesseract is None:
        return list(board.numbered)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def read(cell: Cell, modes: Tuple[int, ...], taken: Set[int]) -> Optional[int]:
        crop = _digit_image(gray, board, cell)
        for mode in modes:
            text = pytesseract.image_to_string(
                crop, config=f"--psm {mode} -c tessedit_char_whitelist=0123456789").strip()
            if text.isdigit() and 1 <= int(text) <= len(board.numbered) and int(text) not in taken:
                return int(text)
        return None

    def read_all(cells: List[Cell], modes: Tuple[int, ...], taken: Set[int]) -> Dict[Cell, int]:
        # Each read launches tesseract, so run them side by side
        with ThreadPoolExecutor(max_workers=8) as pool:
            values = list(pool.map(lambda cell: read(cell, modes, taken), cells))
        return {cell: n for cell, n in zip(cells, values) if n is not None and values.count(n) == 1}

    # Reading the disc as a line of text (mode 7) is the most reliable. Whatever
    # that misses gets a second go as a single word (8) or character (10),
    # which misread more often, so only numbers nobody has claimed yet count.
    board.numbers = read_all(board.numbered, (7,), set())
    unread = [cell for cell in board.numbered if cell not in board.numbers]
    if unread:
        board.numbers.update(read_all(unread, (8, 10), set(board.numbers.values())))
    unread = [cell for cell in board.numbered if cell not in board.numbers]
    missing = set(range(1, len(board.numbered) + 1)) - set(board.numbers.values())
    if len(unread) == 1 and len(missing) == 1:
        # Only one number is unaccounted for, so it must be this cell
        board.numbers[unread.pop()] = missing.pop()
    return unread


def _digit_image(gray: np.ndarray, board: Board, cell: Cell) -> np.ndarray:
    """Cut the digits out of a number disc as black text on white, sized for OCR."""
    cx, cy = board.center(cell)
    radius = max(4, int(board.cell_size * 0.22))    # stays inside the disc
    crop = gray[cy - radius:cy + radius + 1, cx - radius:cx + radius + 1].copy()

    # Blank everything outside the disc so only the white digits remain
    yy, xx = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    crop[xx * xx + yy * yy > radius * radius] = 0

    scale = 96 / crop.shape[0]
    crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    crop = np.where(crop > 128, 0, 255).astype(np.uint8)
    return cv2.copyMakeBorder(crop, 16, 16, 16, 16, cv2.BORDER_CONSTANT, value=255)


def annotate(img: np.ndarray, board: Board, path: Optional[List[Cell]] = None) -> np.ndarray:
    """Draw what was detected (grid, numbers, walls, solution) on a crop of the board."""
    out = img.copy()
    left, right = round(board.xs[0]), round(board.xs[-1])
    top, bottom = round(board.ys[0]), round(board.ys[-1])
    for x in board.xs:
        cv2.line(out, (round(x), top), (round(x), bottom), (0, 200, 0), 1)
    for y in board.ys:
        cv2.line(out, (left, round(y)), (right, round(y)), (0, 200, 0), 1)
    for a, b in board.walls:
        (ax, ay), (bx, by) = board.center(a), board.center(b)
        mx, my, half = (ax + bx) // 2, (ay + by) // 2, round(board.cell_size / 2)
        if a[0] == b[0]:
            cv2.line(out, (mx, my - half), (mx, my + half), (0, 0, 255), 3)
        else:
            cv2.line(out, (mx - half, my), (mx + half, my), (0, 0, 255), 3)
    if path:
        points = np.array([board.center(cell) for cell in path], np.int32)
        cv2.polylines(out, [points], False, (255, 120, 0), 3)
    for cell in board.numbered:
        cx, cy = board.center(cell)
        label = str(board.numbers.get(cell, "?"))
        cv2.putText(out, label, (cx + 8, cy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    margin = round(board.cell_size / 2)
    return out[max(0, top - margin):bottom + margin, max(0, left - margin):right + margin]
