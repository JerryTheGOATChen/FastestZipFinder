"""Solver for LinkedIn Zip.

A Zip puzzle asks for a single path that starts on 1, visits the numbered
cells in increasing order, never crosses a wall, covers every cell exactly
once and ends on the highest number. That is a Hamiltonian path with waypoint
constraints, found here by depth-first search with backtracking.

Cells are indexed row-major (row * cols + col) so that a set of cells fits in
the bits of one int.
"""
import random
from typing import Dict, Iterable, List, Optional, Tuple

Cell = Tuple[int, int]
Wall = Tuple[Cell, Cell]


class _OutOfSteps(Exception):
    """A search used up its step budget without an answer."""


def solve(rows: int, cols: int, numbers: Dict[Cell, int],
          walls: Iterable[Wall] = ()) -> Optional[List[Cell]]:
    """
    Find the path through the board.

    Args:
        rows, cols: Grid dimensions
        numbers: Dict mapping (row, col) -> number shown in that cell
        walls: Pairs of adjacent cells that the path may not step between

    Returns:
        List of (row, col) cells from 1 to the last number, or None if the
        puzzle has no solution.
    """
    ordered = sorted(numbers, key=numbers.get)
    if [numbers[cell] for cell in ordered] != list(range(1, len(ordered) + 1)):
        raise ValueError(f"Numbers must be 1..N with no gaps or repeats, got {sorted(numbers.values())}")
    if len(ordered) < 2:
        raise ValueError("Need at least two numbered cells")

    blocked = set()
    for a, b in walls:
        blocked.add((a, b))
        blocked.add((b, a))

    neighbour_mask = [0] * (rows * cols)
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and ((r, c), (nr, nc)) not in blocked:
                    neighbour_mask[r * cols + c] |= 1 << (nr * cols + nc)

    waypoints = [r * cols + c for r, c in ordered]

    # A depth-first search that guesses wrong early can stay lost for a long
    # time, while the same puzzle walked from the other end, or with ties
    # broken differently, is often easy. So give each attempt a step budget
    # and restart with a bigger one until an attempt finishes.
    budget = 500
    rng = random.Random(0)  # seeded, so the same puzzle always takes the same time
    while True:
        for backwards in (False, True):
            try:
                path = _search(cols, neighbour_mask, waypoints[::-1] if backwards else waypoints, budget, rng)
            except _OutOfSteps:
                continue
            if path is None:
                return None
            return [divmod(cell, cols) for cell in (path[::-1] if backwards else path)]
        budget *= 2


def _search(cols: int, neighbour_mask: List[int], waypoints: List[int], budget: int,
            rng: random.Random) -> Optional[List[int]]:
    """
    Depth-first search for a path that covers every cell and passes the
    waypoints in the order given. Returns None if there is none, raises
    _OutOfSteps after `budget` steps.
    """
    total = len(neighbour_mask)
    full = (1 << total) - 1
    start, last = waypoints[0], waypoints[-1]
    order = [-1] * total    # order[cell] is the cell's position in waypoints, -1 if unnumbered
    for position, cell in enumerate(waypoints):
        order[cell] = position
    numbered_mask = sum(1 << cell for cell in waypoints)

    # Checkerboard colouring: every step of the path lands on the other colour
    colour_mask = [0, 0]
    for cell in range(total):
        colour_mask[sum(divmod(cell, cols)) % 2] |= 1 << cell

    path = [start]
    steps = 0

    def flood(seeds: int, allowed: int) -> int:
        """All cells of `allowed` connected to `seeds`."""
        frontier = seen = seeds & allowed
        while frontier:
            low = frontier & -frontier
            frontier ^= low
            new = neighbour_mask[low.bit_length() - 1] & allowed & ~seen
            seen |= new
            frontier |= new
        return seen

    def open_moves(current: int, free: int, next_waypoint: int) -> int:
        """Cells worth stepping to next, 0 if the unvisited cells can no longer all be covered."""
        # The rest of the path alternates colours, so the counts have to match up
        other_colour = colour_mask[1 - sum(divmod(current, cols)) % 2]
        if (free & other_colour).bit_count() != (free.bit_count() + 1) // 2:
            return 0

        # The next number must be reachable without stepping on a later one
        target = 1 << waypoints[next_waypoint]
        around_target = neighbour_mask[waypoints[next_waypoint]]
        if not around_target & (flood(neighbour_mask[current], free & ~numbered_mask) | 1 << current):
            return 0

        # Numbered cells may only be entered in order, and the last one only at the very end
        closed = numbered_mask & ~target
        if target == 1 << last and free != target:
            closed |= target
        moves = links_fit(current, free, closed)
        return moves if moves and coverable(current, free) else 0

    def links_fit(current: int, free: int, closed: int) -> int:
        """
        Check that every unvisited cell can still get the links it needs and
        return the cells the head of the path may link to (0 if it cannot work).

        The rest of the path gives each unvisited cell two links to its
        neighbours, and one each to the head of the path and the final number.
        A cell with no links to spare must use all of them, a cell that has
        all it needs drops the others, and that can cascade until some cell
        is left with too few or too many. The head may not link to `closed`.
        """
        cells = free | 1 << current
        options = {}    # cell -> neighbours it could still link to
        used = {}       # cell -> neighbours it must link to
        remaining = cells
        while remaining:
            low = remaining & -remaining
            remaining ^= low
            options[low.bit_length() - 1] = neighbour_mask[low.bit_length() - 1] & cells
            used[low.bit_length() - 1] = 0
        remaining = options[current] & closed
        options[current] &= ~closed
        while remaining:
            low = remaining & -remaining
            remaining ^= low
            options[low.bit_length() - 1] &= ~(1 << current)

        pending = list(options)
        while pending:
            cell = pending.pop()
            needed = 1 if cell == current or cell == last else 2
            if options[cell].bit_count() < needed or used[cell].bit_count() > needed:
                return 0
            if options[cell].bit_count() == needed:
                new, drop = options[cell] & ~used[cell], 0
            elif used[cell].bit_count() == needed:
                new, drop = 0, options[cell] & ~used[cell]
            else:
                continue
            used[cell] = options[cell] = options[cell] & ~drop
            changed = new | drop
            while changed:
                low = changed & -changed
                changed ^= low
                other = low.bit_length() - 1
                if low & new:
                    used[other] |= 1 << cell
                else:
                    options[other] &= ~(1 << cell)
                pending.append(other)
        return options[current]

    def coverable(current: int, free: int) -> bool:
        """
        Check the shape of the unvisited area with one depth-first walk from
        the head of the path (Tarjan's cut vertex algorithm).

        The area has to be in one piece. The path also crosses a cut cell only
        once and never comes back, so a cut cell may hide just one pocket
        behind it and that pocket has to hold exactly the highest numbers:
        everything outside it gets visited first.
        """
        reachable = free | 1 << current
        found = [-1] * total    # order in which the walk discovered each cell
        found[current] = 0
        count = 1
        fail = (-1, 0, 0)

        def walk(cell: int, parent: int) -> Tuple[int, int, int]:
            """Returns (earliest cell reachable from this subtree, how many numbers it holds, lowest of them)."""
            nonlocal count
            found[cell] = earliest = count
            count += 1
            held, lowest = (1, order[cell]) if order[cell] >= 0 else (0, len(waypoints))
            pockets = 0
            around = neighbour_mask[cell] & reachable
            while around:
                low = around & -around
                around ^= low
                other = low.bit_length() - 1
                if other == parent:
                    continue
                if found[other] >= 0:
                    earliest = min(earliest, found[other])
                    continue
                child_earliest, child_held, child_lowest = walk(other, cell)
                if child_earliest < 0:
                    return fail
                earliest = min(earliest, child_earliest)
                held += child_held
                lowest = min(lowest, child_lowest)
                if child_earliest >= found[cell]:
                    # `cell` is the only way into the pocket that starts at `other`
                    pockets += 1
                    if pockets > 1 or not child_held or child_lowest != len(waypoints) - child_held:
                        return fail
                    if order[cell] >= 0 and order[cell] != child_lowest - 1:
                        return fail
            return earliest, held, lowest

        first = neighbour_mask[current] & free
        if not first or walk((first & -first).bit_length() - 1, current)[0] < 0:
            return False
        return count == free.bit_count() + 1

    def extend(current: int, visited: int, next_waypoint: int) -> bool:
        nonlocal steps
        if visited == full:
            return current == last
        steps += 1
        if steps > budget:
            raise _OutOfSteps
        free = full & ~visited
        moves = []
        around = open_moves(current, free, next_waypoint)
        while around:
            low = around & -around
            around ^= low
            cell = low.bit_length() - 1
            moves.append(((neighbour_mask[cell] & free).bit_count(), rng.random(), cell))

        # Try the most constrained cell first, it is the likeliest to get stranded.
        # Ties are broken at random so that a restart explores a different order.
        for _, _, cell in sorted(moves):
            path.append(cell)
            if extend(cell, visited | 1 << cell, next_waypoint + (order[cell] >= 0)):
                return True
            path.pop()
        return False

    return path if extend(start, 1 << start, 1) else None


def render(path: List[Cell], rows: int, cols: int, numbers: Dict[Cell, int]) -> str:
    """Draw the solved board as text, numbers in place and the path as lines."""
    up, down, left, right = (-1, 0), (1, 0), (0, -1), (0, 1)
    glyphs = {
        frozenset({up, down}): "│", frozenset({left, right}): "─",
        frozenset({up, right}): "└", frozenset({up, left}): "┘",
        frozenset({down, right}): "┌", frozenset({down, left}): "┐",
    }
    links = {cell: set() for cell in path}
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        links[(r1, c1)].add((r2 - r1, c2 - c1))
        links[(r2, c2)].add((r1 - r2, c1 - c2))

    lines = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            link = links.get((r, c), set())
            if (r, c) in numbers:
                middle = str(numbers[(r, c)])
            else:
                middle = glyphs.get(frozenset(link), "·")
            fill = "─" if right in link else " "
            line += ("─" if left in link else " ") + middle.ljust(2, fill) + fill
        lines.append(line.rstrip())
    return "\n".join(lines)
