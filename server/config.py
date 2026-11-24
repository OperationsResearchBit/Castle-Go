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