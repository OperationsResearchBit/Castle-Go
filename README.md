# Castle-Go
Castle Go game:  
https://operationsresearchbit.github.io/Castle-Go/main.html

agpl3 license

to do
- add vs ai mode
- create game viewer ui on the welcome page
-  add sound effects

# Castle Go  
A real-time two-player strategy game: knights build ringforts and kingdoms on a 9x9 board.


## How to Play

**Phase 1: Maneuvers** (Building)
- Click a knight to select it, then click an empty cell to move it
- Movement follows chess knight rules (L-shape: 2+1)
- Landing on a cell claims it as a ringfort of your color
- Phase ends when both players have no legal moves

**Phase 2: Battle** (Connecting & Capturing)
- Each turn: move a knight (same L-shape rules) AND build one bridge
- Move onto an enemy ringfort or knight to capture it
- Build bridges between adjacent ringforts of your color to form kingdoms
- Game ends when one player captures all enemy knights or no moves remain
- Winner: player with fewer separate kingdoms (groups of connected ringforts)

## Files

- **index.html** — Layout and UI
- **database.js** — Supabase login, sync, leaderboard
- **game-engine.py** — Match class, rules, board rendering

## Multiplayer

- First player to enter a lobby code plays Amber throne
- Second player plays Cyan throne
- Moves sync in real-time across both browsers
- Hall of Fame tracks wins across all completed matches

-----------

Directory structure:  
project-folder/  
  ├── index.html  
  ├── database.js  
  └── game-engine.py  

  



