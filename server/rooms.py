"""A Room is one running match: players, game state, and bot turns."""

import asyncio
import random
import uuid

from .bots import RandomBot
from .config import BOT_NAMES, BOT_THINK_SECONDS, MODES
from .engine import IllegalMove, make_engine
from .players import Player

ROOMS: dict = {}  # room_id -> Room


def _build_turn_order(team_size: int, teams: int) -> list:
    """Alternate between teams: 2v2 gives [0, 2, 1, 3] (A, B, A, B)."""
    order = []
    for slot in range(team_size):
        for team in range(teams):
            order.append(team * team_size + slot)
    return order


def _make_bots(count: int, taken_names: set) -> list:
    available = [n for n in BOT_NAMES if n not in taken_names]
    random.shuffle(available)
    return [Player(name=available[i % len(available)], is_bot=True) for i in range(count)]


async def create_room(mode: str, humans: list) -> "Room":
    """Pad the humans with bots, shuffle seats, and start the match."""
    config = MODES[mode]
    bots = _make_bots(config.players_needed - len(humans), {p.name for p in humans})

    everyone = humans + bots
    random.shuffle(everyone)  # so humans don't always sit on the same team

    for seat, player in enumerate(everyone):
        player.seat = seat
        player.team = seat // config.team_size

    room = Room(mode, everyone)
    ROOMS[room.id] = room
    await room.start()
    return room


class Room:
    def __init__(self, mode: str, players_by_seat: list):
        config = MODES[mode]
        self.id = uuid.uuid4().hex[:8]
        self.mode = mode
        self.players = players_by_seat
        self.engine = make_engine()
        self.bot_brain = RandomBot()
        self.finished = False
        self._bot_task = None

        seat_teams = {p.seat: p.team for p in self.players}
        turn_order = _build_turn_order(config.team_size, config.teams)
        self.state = self.engine.create_state(turn_order, seat_teams)

    # ---- helpers ----------------------------------------------------------

    def _humans(self) -> list:
        return [p for p in self.players if not p.is_bot and p.websocket is not None]

    async def _broadcast(self, message: dict) -> None:
        for player in self._humans():
            await player.send(message)

    async def _broadcast_state(self) -> None:
        await self._broadcast({
            "type": "state",
            "state": self.engine.public_view(self.state),
        })

    # ---- lifecycle --------------------------------------------------------

    async def start(self) -> None:
        for player in self.players:
            player.room = self

        roster = [p.public() for p in self.players]
        for player in self._humans():
            await player.send({
                "type": "match_found",
                "room_id": self.id,
                "mode": self.mode,
                "you": player.public(),
                "players": roster,
            })
        await self._broadcast_state()
        self._kick_bots()

    async def _finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        await self._broadcast({
            "type": "game_over",
            "winner_team": self.engine.winner_team(self.state),
        })
        for player in self.players:
            player.room = None  # lets humans queue again
        ROOMS.pop(self.id, None)

    # ---- human input ------------------------------------------------------

    async def handle_move(self, player: Player, move) -> None:
        if self.finished:
            return
        try:
            self.state = self.engine.apply_move(self.state, player.seat, move)
        except IllegalMove as error:
            await player.send({"type": "error", "message": str(error)})
            return

        await self._broadcast_state()
        if self.engine.winner_team(self.state) is not None:
            await self._finish()
        else:
            self._kick_bots()

    async def player_left(self, player: Player) -> None:
        """A human disconnected: a bot takes over their seat."""
        player.websocket = None
        player.is_bot = True
        player.room = None

        if not self._humans():
            self.finished = True      # nobody left to play for
            ROOMS.pop(self.id, None)
            return
        self._kick_bots()

    # ---- bot turns --------------------------------------------------------

    def _kick_bots(self) -> None:
        """Start the bot runner unless it is already running."""
        if self._bot_task is None or self._bot_task.done():
            self._bot_task = asyncio.create_task(self._run_bots())

    async def _run_bots(self) -> None:
        """Keep playing bot turns until it is a human's turn or the game ends."""
        while not self.finished:
            seat = self.engine.current_seat(self.state)
            if not self.players[seat].is_bot:
                return  # human's turn

            await asyncio.sleep(random.uniform(*BOT_THINK_SECONDS))
            if self.finished:
                return

            # Re-check: the seat may have changed while the bot was "thinking".
            seat = self.engine.current_seat(self.state)
            if not self.players[seat].is_bot:
                return

            move = self.bot_brain.choose_move(self.engine, self.state, seat)
            if move is None:
                return
            self.state = self.engine.apply_move(self.state, seat, move)

            await self._broadcast_state()
            if self.engine.winner_team(self.state) is not None:
                await self._finish()
                return