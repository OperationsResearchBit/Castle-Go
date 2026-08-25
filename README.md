# Castle-Go
Castle Go game:  
https://operationsresearchbit.github.io/Castle-Go/

agpl3 license

to do
- add vs ai hard mode
- create game viewer ui on the welcome page
-  add sound effects, voiceless, move and selection sounds
- make into app apk
- add rules description to the game
- add paid to the DEMO Premium mode

more to do:
modes- battle royale (MMO), 4 player, 4X strategy castle builder    

premium-mode planned: </br>
purchase and earn in-game currency, purchase avatars with in-game currency </br>
member mode to earn more from each game </br>
save 3 replays, download saved or the last replay  

# Castle Go  
A real-time two-player strategy game: knights build ringforts and kingdoms on a 9x9 board.


## How to Play

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/L6NrpGfgFSw/0.jpg)](https://www.youtube.com/watch?v=L6NrpGfgFSw)

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

## How to Play

**Joining a Match (Multiplayer)**
1. Enter your ruler name and a 4-letter lobby code
2. First player to enter a code plays Amber throne (moves first)
3. Second player entering the same code joins as Cyan throne
4. Moves sync in real-time across both browsers
5. Hall of Fame tracks wins across all completed matches

**Practice Mode (vs AI)**
1. Choose "Practice vs AI" on the login screen
2. Enter your name and pick a color
3. AI opponent moves automatically with basic strategy
4. Perfect for learning the rules and testing strategies

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
- **Winner:** player with fewer separate kingdoms (groups of connected ringforts)

## Features

- Real-time multiplayer with instant board sync
- Global Hall of Fame leaderboard
- Practice mode with AI opponent
- Responsive design (desktop & tablet)
- Real-time realtime updates via Supabase

--------------------

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

# Castle Go

A real-time two-player strategy game: knights build ringforts and kingdoms on a 9x9 board.

**Play online:** https://github.com/OperationsResearchBit/Castle-Go

**GitHub:** https://github.com/OperationsResearchBit/Castle-Go

Sign up with any name and a 4-letter lobby code to join or create a match.

--------------------

## For Developers

**Files:**
- `index.html` — Layout, UI, mode selection
- `database.js` — Supabase integration (login, sync, leaderboard)
- `game-engine.py` — Game rules, board state, rendering
- `ai-engine.py` — AI opponent logic

**Tech Stack:**
- Frontend: HTML + Tailwind CSS + PyScript
- Backend: Supabase (PostgreSQL + Realtime)
- Game Logic: Python
  



