"""
Game rules live here, and ONLY here.

To use your real Castle-Go rules, write a class with these same methods
and change `make_engine()` at the bottom. Everything else (matchmaking,
rooms, bots, networking) stays untouched.

Contract:
    create_state(turn_order, seat_teams) -> state
    current_seat(state)                  -> seat whose turn it is
    legal_moves(state, seat)             -> list of moves (empty if not allowed)
    apply_move(state, seat, move)        -> NEW state (raise IllegalMove if bad)
    winner_team(state)                   -> team number, or None while playing
    public_view(state)                   -> JSON-safe dict sent to clients

State should be treated as immutable: apply_move returns a new state.
"""


class IllegalMove(Exception):
    pass


class RaceTo21Engine:
    """Placeholder game so the full pipeline can be tested.

    Players take turns adding 1, 2 or 3 to a shared total.
    The team that pushes the total to 21 or more wins.
    """

    TARGET = 21
    VALID_MOVES = (1, 2, 3)

    def create_state(self, turn_order: list, seat_teams: dict) -> dict:
        return {
            "total": 0,
            "turn_order": turn_order,    # e.g. [0, 2, 1, 3] for 2v2
            "turn_index": 0,
            "seat_teams": seat_teams,    # {seat: team}
            "winner_team": None,
            "last_move": None,
        }

    def current_seat(self, state: dict) -> int:
        return state["turn_order"][state["turn_index"]]

    def winner_team(self, state: dict):
        return state["winner_team"]

    def legal_moves(self, state: dict, seat: int) -> list:
        if state["winner_team"] is not None:
            return []
        if seat != self.current_seat(state):
            return []
        return list(self.VALID_MOVES)

    def apply_move(self, state: dict, seat: int, move) -> dict:
        is_plain_int = isinstance(move, int) and not isinstance(move, bool)
        if not is_plain_int or move not in self.legal_moves(state, seat):
            raise IllegalMove("That move is not allowed right now.")

        new_state = dict(state)
        new_state["total"] = state["total"] + move
        new_state["last_move"] = {"seat": seat, "move": move}

        if new_state["total"] >= self.TARGET:
            new_state["winner_team"] = state["seat_teams"][seat]
        else:
            next_index = (state["turn_index"] + 1) % len(state["turn_order"])
            new_state["turn_index"] = next_index
        return new_state

    def public_view(self, state: dict) -> dict:
        return {
            "total": state["total"],
            "target": self.TARGET,
            "current_seat": self.current_seat(state),
            "winner_team": state["winner_team"],
            "last_move": state["last_move"],
        }


def make_engine():
    """Swap in CastleGoEngine() here once you've written it."""
    return RaceTo21Engine()