import os
import shutil
import unittest

import cv2

import vision

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
HAS_TESSERACT = bool(shutil.which("tesseract")) or os.path.exists(vision.TESSERACT_DEFAULT)

# LinkedIn Zip no. 562, as shown in board_6x6.jpg
NUMBERS = {(1, 1): 1, (1, 4): 2, (2, 4): 3, (2, 1): 4, (3, 4): 5, (3, 1): 6, (4, 4): 7, (4, 1): 8}
WALLS = {((row, col), (row + 1, col)) for row in range(5) for col in (2, 3)}


def load(name):
    return cv2.imread(os.path.join(FIXTURES, name))


class FindBoardTest(unittest.TestCase):
    def test_reads_grid_numbers_and_walls(self):
        board = vision.find_board(load("board_6x6.jpg"))
        self.assertEqual((board.rows, board.cols), (6, 6))
        self.assertEqual(board.numbered, sorted(NUMBERS))
        self.assertEqual(board.walls, WALLS)
        # The 1 sits at (285, 206) in the screenshot
        x, y = board.center((1, 1))
        self.assertAlmostEqual(x, 285, delta=3)
        self.assertAlmostEqual(y, 206, delta=3)

    def test_works_on_a_scaled_screenshot(self):
        img = load("board_6x6.jpg")
        for factor in (0.75, 1.5):
            board = vision.find_board(cv2.resize(img, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA))
            self.assertEqual((board.rows, board.cols), (6, 6))
            self.assertEqual(board.numbered, sorted(NUMBERS))
            self.assertEqual(board.walls, WALLS)

    def test_ignores_a_board_with_a_path_on_it(self):
        self.assertIsNone(vision.find_board(load("board_in_progress.jpg")))

    def test_ignores_a_screen_without_a_board(self):
        self.assertIsNone(vision.find_board(load("start_screen.jpg")))

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract-OCR is not installed")
    def test_reads_the_numbers(self):
        img = load("board_6x6.jpg")
        board = vision.find_board(img)
        self.assertEqual(vision.read_numbers(img, board), [])
        self.assertEqual(board.numbers, NUMBERS)


if __name__ == "__main__":
    unittest.main()
