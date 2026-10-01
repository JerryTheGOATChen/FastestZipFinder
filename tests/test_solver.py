import unittest

import solver

# LinkedIn Zip no. 562, the board in tests/fixtures/board_6x6.jpg
NUMBERS = {(1, 1): 1, (1, 4): 2, (2, 4): 3, (2, 1): 4, (3, 4): 5, (3, 1): 6, (4, 4): 7, (4, 1): 8}
WALLS = {((row, col), (row + 1, col)) for row in range(5) for col in (2, 3)}


class SolveTest(unittest.TestCase):
    def assert_valid(self, path, rows, cols, numbers, walls):
        self.assertEqual(len(path), rows * cols)
        self.assertEqual(len(set(path)), rows * cols, "a cell was visited twice")
        blocked = {frozenset(wall) for wall in walls}
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1, f"{a} -> {b} is not one step")
            self.assertNotIn(frozenset((a, b)), blocked, f"{a} -> {b} crosses a wall")
        self.assertEqual([numbers[cell] for cell in path if cell in numbers], list(range(1, len(numbers) + 1)))
        self.assertEqual(numbers[path[0]], 1)
        self.assertEqual(numbers[path[-1]], len(numbers))

    def test_real_puzzle(self):
        path = solver.solve(6, 6, NUMBERS, WALLS)
        self.assert_valid(path, 6, 6, NUMBERS, WALLS)

    def test_walls(self):
        # On a 3x2 board the only way from corner to corner is to snake down
        numbers = {(0, 0): 1, (2, 1): 2}
        snake = [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0), (2, 1)]
        self.assertEqual(solver.solve(3, 2, numbers), snake)
        self.assertEqual(solver.solve(3, 2, numbers, {((0, 0), (1, 0))}), snake)
        # A wall given in either order blocks the step in both directions
        self.assertIsNone(solver.solve(3, 2, numbers, {((1, 1), (1, 0))}))
        self.assertIsNone(solver.solve(3, 2, numbers, {((1, 0), (1, 1))}))

    def test_no_solution(self):
        # A path over 9 cells has to end on the colour it started on, (0, 1) is the other one
        self.assertIsNone(solver.solve(3, 3, {(0, 0): 1, (0, 1): 2}))

    def test_larger_board(self):
        snake = [(row, col) for row in range(8) for col in (range(8) if row % 2 == 0 else range(7, -1, -1))]
        numbers = {snake[index]: n for n, index in enumerate((0, 9, 22, 30, 41, 55, 63), start=1)}
        self.assert_valid(solver.solve(8, 8, numbers), 8, 8, numbers, ())

    def test_rejects_bad_numbers(self):
        with self.assertRaises(ValueError):
            solver.solve(3, 3, {(0, 0): 1, (2, 2): 3})
        with self.assertRaises(ValueError):
            solver.solve(3, 3, {(0, 0): 1})

    def test_render(self):
        path = [(0, 0), (0, 1), (1, 1), (1, 0)]
        self.assertEqual(solver.render(path, 2, 2, {(0, 0): 1, (1, 0): 2}), " 1───┐\n 2───┘")


if __name__ == "__main__":
    unittest.main()
