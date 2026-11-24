<#
.SYNOPSIS
    Creates the Castle-Go matchmaking server architecture in the current folder.

.USAGE
    Run from the project ROOT (the folder that contains index.html and capacitor.config.json):

        powershell -ExecutionPolicy Bypass -File .\setup-server.ps1
        powershell -ExecutionPolicy Bypass -File .\setup-server.ps1 -Force   # overwrite existing files

    Result:
        ./requirements.txt
        ./test_flow.py
        ./battle.js
        ./server/__init__.py
        ./server/config.py
        ./server/players.py
        ./server/engine.py
        ./server/bots.py
        ./server/matchmaker.py
        ./server/rooms.py
        ./server/main.py
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-ProjectFile {
    param(
        [string]$RelativePath,
        [string]$Content
    )

    $fullPath = Join-Path $Root $RelativePath
    $folder = Split-Path $fullPath -Parent

    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }

    if ((Test-Path $fullPath) -and (-not $Force)) {
        Write-Host "  skipped (exists)  $RelativePath" -ForegroundColor Yellow
        return
    }

    # Normalise to Windows line endings, no BOM.
    $text = ($Content -replace "`r`n", "`n") -replace "`n", "`r`n"
    [System.IO.File]::WriteAllText($fullPath, $text, $Utf8NoBom)
    Write-Host "  created           $RelativePath" -ForegroundColor Green
}

Write-Host ""
Write-Host "Scaffolding Castle-Go server in: $Root" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------------------
# requirements.txt
# ---------------------------------------------------------------------------
Write-ProjectFile "requirements.txt" @'
fastapi
uvicorn[standard]
websockets
'@

# ---------------------------------------------------------------------------
# server/__init__.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/__init__.py" @'
'@

# ---------------------------------------------------------------------------
# server/config.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/config.py" @'
"""Tunable settings. Change numbers here, not in the logic files."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeConfig:
    team_size: int          # players per team
    teams: int = 2          # number of teams

    @property
    def players_needed(self) -> int:
        return self.team_size * self.teams


MODES = {
    "1v1": ModeConfig(team_size=1),
    "2v2": ModeConfig(team_size=2),
}

# How long a player waits for real humans before bots fill the empty seats.
QUEUE_TIMEOUT_SECONDS = 3.0

# How often the matchmaker checks the queues.
MATCHMAKER_TICK_SECONDS = 0.25

# Bots "think" for a random time in this range so they feel human.
BOT_THINK_SECONDS = (0.6, 1.4)

BOT_NAMES = [
    "Knight_Rex", "Moat_Walker", "TowerTom", "SirLagsALot", "DragonBait",
    "CastleCat", "Pawn_Star", "RookieRook", "Duke_Nukem", "LadyLance",
    "Bishop_Bob", "SiegeSally", "CrownJules", "Drawbridge", "GoGoGuard",
]

MAX_NAME_LENGTH = 16
'@

# ---------------------------------------------------------------------------
# server/players.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/players.py" @'
"""A Player is either a connected human or a server-controlled bot."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(eq=False)  # eq=False -> players are compared by identity
class Player:
    name: str
    websocket: Any = None
    is_bot: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    # Matchmaking state
    queue_mode: Optional[str] = None
    queued_at: float = 0.0

    # Match state
    room: Any = None
    seat: int = -1
    team: int = -1

    async def send(self, message: dict) -> None:
        """Send JSON to a human. Bots and dead sockets are silently skipped."""
        if self.websocket is None:
            return
        try:
            await self.websocket.send_json(message)
        except Exception:
            pass  # the disconnect handler will clean up

    def public(self) -> dict:
        """What other players are allowed to know about this player.
        is_bot is deliberately NOT included, so bots look like humans."""
        return {"id": self.id, "name": self.name, "seat": self.seat, "team": self.team}
'@

# ---------------------------------------------------------------------------
# server/engine.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/engine.py" @'
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
'@

# ---------------------------------------------------------------------------
# server/bots.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/bots.py" @'
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
'@

# ---------------------------------------------------------------------------
# server/matchmaker.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/matchmaker.py" @'
"""
Queue logic: pair humans quickly, and give up waiting after a timeout.

Everything runs on one asyncio event loop, and the queue methods contain
no `await`, so no locks are needed.
"""

import asyncio
import time
from typing import Awaitable, Callable

from .config import MATCHMAKER_TICK_SECONDS, MODES, QUEUE_TIMEOUT_SECONDS
from .players import Player

# Called with (mode, list_of_humans) when a match is ready.
MatchCallback = Callable[[str, list], Awaitable[None]]


class Matchmaker:
    def __init__(self, on_match: MatchCallback):
        self.on_match = on_match
        self.queues = {mode: [] for mode in MODES}

    # ---- queue operations -------------------------------------------------

    def enqueue(self, player: Player, mode: str) -> None:
        player.queue_mode = mode
        player.queued_at = time.monotonic()
        self.queues[mode].append(player)

    def cancel(self, player: Player) -> None:
        if player.queue_mode is None:
            return
        queue = self.queues[player.queue_mode]
        if player in queue:
            queue.remove(player)
        player.queue_mode = None

    # ---- matching ---------------------------------------------------------

    def _pull_ready_groups(self, mode: str) -> list:
        """Return groups of humans that should start a match right now."""
        needed = MODES[mode].players_needed
        queue = self.queues[mode]
        groups = []

        # 1) Full groups of real humans start instantly.
        while len(queue) >= needed:
            groups.append([queue.pop(0) for _ in range(needed)])

        # 2) Leftover players who waited too long start with bot backfill.
        if queue:
            waited = time.monotonic() - queue[0].queued_at
            if waited >= QUEUE_TIMEOUT_SECONDS:
                groups.append(list(queue))
                queue.clear()

        for group in groups:
            for player in group:
                player.queue_mode = None
        return groups

    async def run(self) -> None:
        """Background loop; started once when the server boots."""
        while True:
            await asyncio.sleep(MATCHMAKER_TICK_SECONDS)
            for mode in MODES:
                for humans in self._pull_ready_groups(mode):
                    try:
                        await self.on_match(mode, humans)
                    except Exception as error:  # never let one bad match kill the loop
                        print(f"[matchmaker] failed to start match: {error!r}")
'@

# ---------------------------------------------------------------------------
# server/rooms.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/rooms.py" @'
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
'@

# ---------------------------------------------------------------------------
# server/main.py
# ---------------------------------------------------------------------------
Write-ProjectFile "server/main.py" @'
"""
Entry point. Run from the project root with:
    uvicorn server.main:app --host 0.0.0.0 --port 8000
Keep ONE worker for now: matchmaking and rooms live in this process's memory.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .config import MAX_NAME_LENGTH, MODES, QUEUE_TIMEOUT_SECONDS
from .matchmaker import Matchmaker
from .players import Player
from .rooms import ROOMS, create_room


async def on_match(mode: str, humans: list) -> None:
    await create_room(mode, humans)


matchmaker = Matchmaker(on_match)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(matchmaker.run())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "rooms": len(ROOMS),
        "queued": {mode: len(q) for mode, q in matchmaker.queues.items()},
    }


def clean_name(raw) -> str:
    if not isinstance(raw, str):
        return ""
    return raw.strip()[:MAX_NAME_LENGTH]


async def handle_message(player: Player, message: dict) -> None:
    kind = message.get("type")

    if kind == "queue":
        if player.room is not None or player.queue_mode is not None:
            await player.send({"type": "error", "message": "Already queued or in a match."})
            return
        mode = message.get("mode", "1v1")
        if mode not in MODES:
            await player.send({"type": "error", "message": f"Unknown mode: {mode}"})
            return
        player.name = clean_name(message.get("name")) or player.name
        matchmaker.enqueue(player, mode)
        await player.send({"type": "queued", "mode": mode, "max_wait": QUEUE_TIMEOUT_SECONDS})

    elif kind == "cancel":
        matchmaker.cancel(player)
        await player.send({"type": "queue_cancelled"})

    elif kind == "move":
        if player.room is not None:
            await player.room.handle_move(player, message.get("move"))

    elif kind == "ping":
        await player.send({"type": "pong"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    player = Player(name=f"Player{len(ROOMS) + 1}", websocket=websocket)
    await player.send({"type": "hello", "id": player.id, "modes": list(MODES)})

    try:
        while True:
            message = await websocket.receive_json()
            if isinstance(message, dict):
                await handle_message(player, message)
    except WebSocketDisconnect:
        pass
    except Exception as error:
        print(f"[ws] connection error: {error!r}")
    finally:
        matchmaker.cancel(player)
        if player.room is not None:
            await player.room.player_left(player)
'@

# ---------------------------------------------------------------------------
# battle.js  (client; sits next to index.html, copy into dist/ for Capacitor)
# ---------------------------------------------------------------------------
Write-ProjectFile "battle.js" @'
// battle.js: load next to index.html with <script src="battle.js"></script>

// Local dev:   ws://localhost:8000/ws
// Codespaces:  wss://<codespace-name>-8000.app.github.dev/ws  (set port 8000 to Public)
// Production:  wss://your-server.example.com/ws
// Don't auto-detect "localhost": a Capacitor app also reports localhost.
const SERVER_URL = "ws://localhost:8000/ws";

const Battle = {
  socket: null,
  me: null,          // { id, name, seat, team }
  players: [],       // everyone in the current match
  mode: "1v1",

  // ---- hooks: assign these from your game code ----------------------------
  onStatus(text) {},                        // update the "Searching..." label
  onMatchStart(info) {},                    // { me, players, mode }: show the board
  onState(state) {},                        // redraw the board from server state
  onGameOver(winnerTeam, didWin) {},        // show the result screen
  onError(message) {},

  // ---- connection ---------------------------------------------------------
  connect() {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(SERVER_URL);
      this.socket.onopen = () => resolve();
      this.socket.onerror = () => reject(new Error("Could not reach server"));
      this.socket.onmessage = (event) => this._handle(JSON.parse(event.data));
      this.socket.onclose = () => this.onStatus("Disconnected");
    });
  },

  _send(payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  },

  // ---- actions your UI calls ----------------------------------------------
  async battle(mode, name) {
    this.mode = mode;
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.onStatus("Connecting...");
      await this.connect();
    }
    this.onStatus("Searching for opponents...");
    this._send({ type: "queue", mode, name });
  },

  cancel() {
    this._send({ type: "cancel" });
  },

  sendMove(move) {
    this._send({ type: "move", move });
  },

  // ---- incoming messages --------------------------------------------------
  _handle(message) {
    switch (message.type) {
      case "queued":
        this.onStatus("Searching...");
        break;
      case "queue_cancelled":
        this.onStatus("");
        break;
      case "match_found":
        this.me = message.you;
        this.players = message.players;
        this.onMatchStart({ me: this.me, players: this.players, mode: message.mode });
        break;
      case "state":
        this.onState(message.state);
        break;
      case "game_over":
        this.onGameOver(message.winner_team, message.winner_team === this.me.team);
        break;
      case "error":
        this.onError(message.message);
        break;
    }
  },
};
'@

# ---------------------------------------------------------------------------
# test_flow.py
# ---------------------------------------------------------------------------
Write-ProjectFile "test_flow.py" @'
"""
Run the server in one terminal, then in another:  python test_flow.py
Test A: one human alone -> bots must fill in after about 3 seconds.
Test B: two humans in 1v1 -> they should be matched immediately.
"""

import asyncio
import json
import time

import websockets

URL = "ws://localhost:8000/ws"


async def play(label: str, mode: str = "1v1") -> None:
    started = time.monotonic()
    async with websockets.connect(URL) as ws:
        await ws.send(json.dumps({"type": "queue", "mode": mode, "name": label}))
        me = None
        async for raw in ws:
            msg = json.loads(raw)

            if msg["type"] == "match_found":
                me = msg["you"]
                waited = time.monotonic() - started
                print(f"[{label}] matched after {waited:.1f}s as seat {me['seat']}")

            elif msg["type"] == "state" and me:
                state = msg["state"]
                if state["winner_team"] is None and state["current_seat"] == me["seat"]:
                    await ws.send(json.dumps({"type": "move", "move": 3}))

            elif msg["type"] == "game_over":
                print(f"[{label}] game over, winner team {msg['winner_team']}")
                return


async def main() -> None:
    print("--- Test A: solo player gets bots ---")
    await play("Solo")
    print("--- Test B: two humans matched instantly ---")
    await asyncio.gather(play("Alice"), play("Bob"))


asyncio.run(main())
'@

# ---------------------------------------------------------------------------
# .gitignore additions (only adds lines that are missing)
# ---------------------------------------------------------------------------
$gitignorePath = Join-Path $Root ".gitignore"
$wanted = @(".venv/", "__pycache__/", "*.pyc")
$existing = @()
if (Test-Path $gitignorePath) { $existing = Get-Content $gitignorePath }
$missing = $wanted | Where-Object { $existing -notcontains $_ }
if ($missing) {
    Add-Content -Path $gitignorePath -Value $missing
    Write-Host "  updated           .gitignore" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done. Next steps:" -ForegroundColor Cyan
Write-Host "  python -m venv .venv"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  pip install -r requirements.txt"
Write-Host "  uvicorn server.main:app --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "Then, in a second PowerShell window (venv activated):"
Write-Host "  python test_flow.py"
Write-Host ""
