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