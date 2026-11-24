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