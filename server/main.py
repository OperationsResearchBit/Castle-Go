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