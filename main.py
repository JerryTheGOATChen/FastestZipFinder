"""
LinkedIn Zip Auto-Solver

Watches the screen for a Zip board, reads it, solves it and plays the
solution into the game. Run it, then start the game in your browser.
"""
import argparse
import sys
import threading
import time

import cv2

import solver
import vision

DEBUG_IMAGE = "zip_debug.png"


def parse_args():
    parser = argparse.ArgumentParser(description="Solve the LinkedIn Zip board that is on screen.")
    parser.add_argument("--dry-run", action="store_true",
                        help="find and solve the board but leave the mouse and keyboard alone")
    parser.add_argument("--mouse", action="store_true",
                        help="drag the path with the mouse instead of using the arrow keys")
    parser.add_argument("--step", type=float, default=0.02, metavar="SECONDS",
                        help="pause between moves, raise it if the game misses some (default: 0.02)")
    parser.add_argument("--timeout", type=float, default=60, metavar="SECONDS",
                        help="how long to wait for a board to show up (default: 60)")
    parser.add_argument("--image", metavar="FILE",
                        help="read the board from a screenshot file instead of the screen (never plays)")
    parser.add_argument("--debug", action="store_true",
                        help=f"save a picture of what was detected to {DEBUG_IMAGE}")
    return parser.parse_args()


def wait_for_board(timeout: float):
    """
    Poll the screen until a board shows up and has stopped changing.
    Returns (image, board, origin, scale) or None on timeout.
    """
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        img, origin, scale = vision.capture_screen()
        board = vision.find_board(img)
        if board and len(board.numbered) < 2:
            board = None
        # The same board twice in a row means the game has finished animating it in
        if board and board.same_puzzle(previous):
            return img, board, origin, scale
        previous = board
        time.sleep(0.1)
    return None


def ask_for_numbers(board: vision.Board, unread):
    """Fall back to the user for the numbers OCR could not make out."""
    print("\nCould not read every number, please fill in the rest (rows and columns count from the top left):")
    for row, col in unread:
        answer = ""
        while not answer.isdigit():
            answer = input(f"  Number at row {row + 1}, column {col + 1}: ").strip()
        board.numbers[(row, col)] = int(answer)


def main() -> int:
    args = parse_args()
    sys.stdout.reconfigure(errors="replace")    # the path drawing may not fit a legacy console encoding

    if args.image:
        img, origin, scale = cv2.imread(args.image), (0, 0), 1.0
        if img is None:
            print(f"Could not open {args.image}")
            return 1
        board = vision.find_board(img)
    else:
        print("Looking for a Zip board on screen, start the game now (Ctrl+C to quit)...")
        threading.Thread(target=vision.warm_up_ocr, daemon=True).start()
        found = wait_for_board(args.timeout)
        img, board, origin, scale = found if found else (None, None, None, None)
    started = time.perf_counter()

    if board is None:
        print("No fresh Zip board found. The whole board has to be visible, in LinkedIn's light theme,")
        print("with no path drawn on it yet (press Reset in the game if there is one).")
        return 1
    print(f"Found a {board.rows}x{board.cols} board with {len(board.numbered)} numbers and {len(board.walls)} walls")

    unread = vision.read_numbers(img, board)
    if unread:
        ask_for_numbers(board, unread)

    try:
        path = solver.solve(board.rows, board.cols, board.numbers, board.walls)
    except ValueError as error:
        print(f"The numbers on the board do not add up: {error}")
        path = None
    if args.debug:
        cv2.imwrite(DEBUG_IMAGE, vision.annotate(img, board, path))
        print(f"Saved what was detected to {DEBUG_IMAGE}")
    if path is None:
        print("No solution found, so the board was probably misread. Run with --debug to see what was detected.")
        return 1
    print(solver.render(path, board.rows, board.cols, board.numbers))

    if args.dry_run or args.image:
        return 0

    import automation   # imported late so --image works on a machine with no display
    points = []
    for cell in path:
        x, y = board.center(cell)
        points.append((round(origin[0] + x / scale), round(origin[1] + y / scale)))
    try:
        if args.mouse:
            automation.play_with_mouse(points, args.step)
        else:
            automation.play_with_keys(path, points[0], args.step)
    except automation.pyautogui.FailSafeException:
        print("Aborted, the mouse was moved to the corner of the screen.")
        return 1
    print(f"Done in {time.perf_counter() - started:.2f}s from spotting the board")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(1)
