"""Plays a solved path into the game, with the arrow keys or by dragging the mouse."""
import time
from typing import List, Tuple

import pyautogui

Cell = Tuple[int, int]
Point = Tuple[int, int]

# Safety: slam the mouse into the top-left corner of the screen to abort
pyautogui.FAILSAFE = True
# No automatic pause after each action, the functions below do their own timing
pyautogui.PAUSE = 0

ARROW_KEYS = {(-1, 0): "up", (1, 0): "down", (0, -1): "left", (0, 1): "right"}


def play_with_keys(path: List[Cell], start: Point, step: float = 0.02):
    """
    Click the first cell, then walk the path with the arrow keys.

    Args:
        path: List of (row, col) cells in the order to visit them
        start: Screen position of the first cell
        step: Pause after each key press (seconds)
    """
    pyautogui.click(*start)
    time.sleep(0.1)     # let the browser focus the board before the keys arrive
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        pyautogui.press(ARROW_KEYS[(r2 - r1, c2 - c1)])
        time.sleep(step)


def play_with_mouse(points: List[Point], step: float = 0.02):
    """
    Hold the left button down and drag through every cell of the path.

    Args:
        points: Screen position of each cell of the path, in order
        step: Pause at each cell so the game registers it (seconds)
    """
    pyautogui.moveTo(*points[0])
    pyautogui.mouseDown()
    try:
        for point in points:
            pyautogui.moveTo(*point)
            time.sleep(step)
    finally:
        pyautogui.mouseUp()
