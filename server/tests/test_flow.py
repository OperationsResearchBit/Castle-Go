"""
Run the server in one terminal, then in another:  python test_flow.py
Test A: one human alone -> bots must fill in after about 3 seconds.
Test B: two humans in 1v1 -> they should be matched immediately.
"""

import asyncio
import json
import time

import websockets

URL = "ws://127.0.0.1:8000/ws"


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
