"""Bot decision-making. Works with any engine through legal_moves()."""

import random


class RandomBot:
    """Picks any legal move. Good enough to start; replace with smarter logic later."""

    def choose_move(self, engine, state, seat):
        moves = engine.legal_moves(state, seat)
        if not moves:
            return None
        return random.choice(moves)


# Later, a smarter bot can look ahead, for example:
#
# class MinimaxBot:
#     def choose_move(self, engine, state, seat):
#         ...try each legal move with engine.apply_move and score the result...