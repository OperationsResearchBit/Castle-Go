# CHANGELOG

## [Unreleased]

## [0.3.0] – Added New Game Mode

I had this on the to do list and it’s now implemented. This release expands the feature set significantly, adding AI difficulty, UI upgrades, premium scaffolding, maps, avatars, QoL improvements, replays, and Conquest Mode progression.

New AI Mode
-	Added VS AI Mode — players can now battle an adaptive AI opponent with full knight/ringfort mechanics.
-	Implemented AI decision engine with basic heuristics (territory pressure, safe knight mobility, capture priority).
-	Added difficulty selector (Easy / Normal / Hard).
-	Updated mode selector UI to include VS AI Arena.
-	Added fallback logic for AI when no legal knight moves remain.

VS Medium AI
-	Added VS Medium AI difficulty tier for smoother progression between Easy and Hard.

Welcome Page Viewer
-	Added Game Viewer UI on the welcome page to preview active matches and states.

Premium Mode Demo
-	Added a 💎 Premium card on the setup screen with an Activate Premium (Demo) toggle.
-	Stored in localStorage; client only placeholder.
-	Replace setPremium() with a real Stripe → Supabase → RLS check before production.
-	Premium Mode is temporary and will be rolled back once payments are enabled.

Expansions & Maps
-	Added two premium maps: Twin Rivers and Highland Siege.
-	Impassable terrain enforced at the rules engine legality level.
-	Map choice is a <select> on Multiplayer + AI forms.
-	Premium maps show a 🔒 and revert to Classic for free users.
-	More details: Premium Maps.

Player Colors & Avatars
-	Added color picker + 10 emoji avatar grid, gated behind premium.
-	Disabled for free users.
-	Colors/avatars sync into the match state for opponents + spectators.
-	More details: Player Avatars.

Quality of Life
-	Added ⛶ Fullscreen button (premium only).
-	Added dismissible ad banner placeholder for free users.
-	More details: Premium QoL.

## [0.2.0] – Added New Game Mode
I had this on the to‑do list and it's done:

- Added **VS AI Mode** — players can now battle an adaptive AI opponent with full knight/ringfort mechanics.
- Implemented AI decision engine with basic heuristics (territory pressure, safe knight mobility, capture priority).
- Added difficulty selector (Easy / Normal / Hard).
- Updated mode selector UI to include “VS AI Arena”.
- Added fallback logic for AI when no legal knight moves remain.

## [0.1.0] – Initial Prototype
- Core 9×9 grid rendering
- Knight movement + ringfort claiming
- Basic capture rules
- Turn system + UI panels
