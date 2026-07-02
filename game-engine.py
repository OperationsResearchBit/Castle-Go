from pyscript import document, window
from pyodide.ffi import create_proxy
import json

KNIGHT_OFFSETS = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
SIZE = 9

COLOR_STYLES = {
    "B": {"bg": "#92400e", "ring": "#fbbf24", "label": "Amber Throne"},
    "W": {"bg": "#0e7490", "ring": "#22d3ee", "label": "Cyan Throne"},
}

class Match:
    def __init__(self):
        self.size = SIZE
        self.board = [["." for _ in range(SIZE)] for _ in range(SIZE)]
        self.bridges = []
        self.phase = 1
        self.current_turn = "B"
        self.turn_step = "move"
        self.winner = None
        self.players = {
            "B": {"name": None, "knights": [[0, 1], [1, 0], [1, 2]]},
            "W": {"name": None, "knights": [[8, 7], [7, 8], [7, 6]]},
        }
        for pos in self.players["B"]["knights"]:
            self.board[pos[0]][pos[1]] = "B"
        for pos in self.players["W"]["knights"]:
            self.board[pos[0]][pos[1]] = "W"
        self.log = "Phase 1: Maneuvers. Black moves first."

    def knight_destinations(self, r, c):
        out = []
        for dr, dc in KNIGHT_OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                out.append((nr, nc))
        return out

    def knight_at(self, r, c):
        for color in ("B", "W"):
            for idx, pos in enumerate(self.players[color]["knights"]):
                if pos[0] == r and pos[1] == c:
                    return (color, idx)
        return None

    def legal_phase1_moves_for(self, color):
        moves = []
        for idx, pos in enumerate(self.players[color]["knights"]):
            r, c = pos[0], pos[1]
            for nr, nc in self.knight_destinations(r, c):
                if self.board[nr][nc] == ".":
                    moves.append((idx, nr, nc))
        return moves

    def legal_phase2_knight_moves_for(self, color):
        moves = []
        for idx, pos in enumerate(self.players[color]["knights"]):
            r, c = pos[0], pos[1]
            for nr, nc in self.knight_destinations(r, c):
                occ = self.knight_at(nr, nc)
                if occ and occ[0] == color:
                    continue
                moves.append((idx, nr, nc))
        return moves

    def has_bridge(self, a, b):
        a, b = list(a), list(b)
        for bridge in self.bridges:
            if (bridge[0] == a and bridge[1] == b) or (bridge[0] == b and bridge[1] == a):
                return True
        return False

    def legal_bridge_pairs_for(self, color):
        pairs = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] != color:
                    continue
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size and self.board[nr][nc] == color:
                        if not self.has_bridge((r, c), (nr, nc)):
                            pairs.append(((r, c), (nr, nc)))
        return pairs

    def count_kingdoms(self, color):
        cells = [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == color]
        parent = {cell: cell for cell in cells}

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for bridge in self.bridges:
            a, b = tuple(bridge[0]), tuple(bridge[1])
            if a in parent and b in parent:
                union(a, b)

        roots = set(find(c) for c in cells)
        return len(roots)

    def to_dict(self):
        return {
            "board": self.board,
            "bridges": self.bridges,
            "phase": self.phase,
            "current_turn": self.current_turn,
            "turn_step": self.turn_step,
            "winner": self.winner,
            "players": self.players,
            "log": self.log,
        }

    @staticmethod
    def from_dict(d):
        m = Match.__new__(Match)
        m.size = SIZE
        m.board = d["board"]
        m.bridges = d["bridges"]
        m.phase = d["phase"]
        m.current_turn = d["current_turn"]
        m.turn_step = d["turn_step"]
        m.winner = d["winner"]
        m.players = d["players"]
        m.log = d["log"]
        return m


def is_adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def has_any_action(m, color):
    if m.legal_phase2_knight_moves_for(color):
        return True
    if m.legal_bridge_pairs_for(color):
        return True
    return False


def finalize_game(m):
    bk = m.count_kingdoms("B")
    wk = m.count_kingdoms("W")
    if bk < wk:
        m.winner = "B"
    elif wk < bk:
        m.winner = "W"
    else:
        m.winner = "draw"
    m.log = (
        f"No more legal actions remain. Final tally: "
        f"{m.players['B']['name']} holds {bk} kingdom(s), "
        f"{m.players['W']['name']} holds {wk} kingdom(s)."
    )


def advance_turn_phase1(m):
    mover = m.current_turn
    other = "W" if mover == "B" else "B"
    if m.legal_phase1_moves_for(other):
        m.current_turn = other
    elif m.legal_phase1_moves_for(mover):
        m.log += f" {m.players[other]['name']} has no legal moves and passes."
    else:
        m.phase = 2
        m.turn_step = "move"
        m.log += " No more legal maneuvers for either side. The Battle Phase begins!"


def end_turn_phase2(m):
    m.turn_step = "move"
    mover = m.current_turn
    other = "W" if mover == "B" else "B"
    if has_any_action(m, other):
        m.current_turn = other
    elif has_any_action(m, mover):
        m.log += f" {m.players[other]['name']} has no legal actions and passes."
    else:
        finalize_game(m)


# ---- mutable session state (local to this browser tab) ----
current_match = None
my_color = None
my_name = ""
selected = None
is_vs_ai = False
ai_color = None
ai_mode = "easy"  # "easy" | "medium", set via pySetAIMode


def set_ai_mode(mode):
    """Called from JS when the player picks a difficulty on the setup screen."""
    global ai_mode
    if mode in ("easy", "medium"):
        ai_mode = mode


def run_ai_turn(m, color):
    """Dispatch to the selected difficulty's AI implementation.

    ai_easy.py and ai_medium.py both load into this same global namespace,
    so each of their functions was renamed with an _easy / _medium suffix
    to avoid one silently overwriting the other.
    """
    if ai_mode == "medium":
        return ai_take_turn_medium(m, color)
    return ai_take_turn_easy(m, color)


def handle_phase1_click(m, color, sel, r, c):
    if sel is None:
        knight = m.knight_at(r, c)
        if knight and knight[0] == color:
            return (r, c), False
        return None, False

    sr, sc = sel
    if (r, c) == (sr, sc):
        return None, False

    dests = [d for d in m.knight_destinations(sr, sc) if m.board[d[0]][d[1]] == "."]
    if (r, c) in dests:
        idx = m.knight_at(sr, sc)[1]
        m.players[color]["knights"][idx] = [r, c]
        m.board[r][c] = color
        m.log = f"{m.players[color]['name']} advances a knight to claim new ground."
        advance_turn_phase1(m)
        return None, True

    knight = m.knight_at(r, c)
    if knight and knight[0] == color:
        return (r, c), False
    return sel, False


def handle_phase2_move_click(m, color, sel, r, c):
    enemy = "W" if color == "B" else "B"
    if sel is None:
        knight = m.knight_at(r, c)
        if knight and knight[0] == color:
            return (r, c), False
        return None, False

    sr, sc = sel
    if (r, c) == (sr, sc):
        return None, False

    dests = m.knight_destinations(sr, sc)
    occupant = m.knight_at(r, c)
    if (r, c) in dests and not (occupant and occupant[0] == color):
        idx = m.knight_at(sr, sc)[1]
        captured_knight = occupant
        captured_fort = m.board[r][c] == enemy
        m.players[color]["knights"][idx] = [r, c]
        m.board[r][c] = color
        msgs = [f"{m.players[color]['name']} marches a knight forward."]
        if captured_knight:
            ecolor, eidx = captured_knight
            del m.players[ecolor]["knights"][eidx]
            msgs.append("An enemy knight is captured!")
            if not m.players[ecolor]["knights"]:
                m.winner = color
                msgs.append(f"{m.players[color]['name']} has eliminated all enemy knights and wins!")
        elif captured_fort:
            msgs.append("An enemy ringfort falls under new banners.")
        m.log = " ".join(msgs)
        if not m.winner:
            m.turn_step = "bridge"
            if not m.legal_bridge_pairs_for(color):
                end_turn_phase2(m)
        return None, True

    knight = m.knight_at(r, c)
    if knight and knight[0] == color:
        return (r, c), False
    return sel, False


def handle_phase2_bridge_click(m, color, sel, r, c):
    if sel is None:
        if m.board[r][c] == color:
            return (r, c), False
        return None, False

    sr, sc = sel
    if (r, c) == (sr, sc):
        return None, False

    if m.board[r][c] == color and is_adjacent(sel, (r, c)) and not m.has_bridge(sel, (r, c)):
        m.bridges.append([list(sel), [r, c]])
        m.log = f"{m.players[color]['name']} raises a bridge, uniting their kingdom."
        end_turn_phase2(m)
        return None, True

    if m.board[r][c] == color:
        return (r, c), False
    return sel, False


def record_result(m):
    winner_name = "draw"
    if m.winner in ("B", "W"):
        winner_name = m.players[m.winner]["name"]
    payload = {
        "black_name": m.players["B"]["name"],
        "white_name": m.players["W"]["name"],
        "winner_name": winner_name,
        "black_kingdoms": m.count_kingdoms("B"),
        "white_kingdoms": m.count_kingdoms("W"),
    }
    window.recordResult(json.dumps(payload))


def on_cell_click(r, c):
    global selected
    m = current_match
    if m is None or m.winner:
        return
    if m.current_turn != my_color:
        document.querySelector("#log").innerText = "Hold — it's not your turn yet."
        return

    if m.phase == 1:
        selected, changed = handle_phase1_click(m, my_color, selected, r, c)
    elif m.turn_step == "move":
        selected, changed = handle_phase2_move_click(m, my_color, selected, r, c)
    else:
        selected, changed = handle_phase2_bridge_click(m, my_color, selected, r, c)

    if changed:
        if m.winner:
            record_result(m)
        sync_and_render()
        if is_vs_ai and not m.winner:
            # Schedule AI turn after a brief delay so user can see the board update
            window.setTimeout(create_proxy(lambda: trigger_ai_turn()), 800)
    else:
        draw_board()


def trigger_ai_turn():
    """Called when it's the AI's turn. The AI takes its move automatically."""
    global is_vs_ai
    m = current_match
    if m is None or m.winner or not is_vs_ai or m.current_turn != ai_color:
        return
    
    try:
        run_ai_turn(m, ai_color)
        
        if m.winner:
            record_result(m)
        
        sync_and_render()
        
        # If it's the player's turn now, they can click
        if m.current_turn == my_color:
            document.querySelector("#log").innerText += " → Your turn!"
        elif not m.winner:
            # AI still has moves, schedule next turn
            window.setTimeout(create_proxy(lambda: trigger_ai_turn()), 800)
    except Exception as e:
        import traceback
        error_msg = f"AI error: {str(e)}"
        document.querySelector("#log").innerText = error_msg
        print(f"AI Exception: {error_msg}")


def draw_board():
    m = current_match
    if m is None:
        return
    container = document.querySelector("#grid_board")
    container.innerHTML = ""
    for r in range(m.size):
        for c in range(m.size):
            cell = document.createElement("button")
            owner = m.board[r][c]
            occ = m.knight_at(r, c)

            base = "w-9 h-9 flex items-center justify-center text-base font-bold rounded-sm transition relative "
            if owner == ".":
                base += "bg-gray-800 hover:bg-gray-700"
            else:
                base += "hover:brightness-110"
                cell.style.backgroundColor = COLOR_STYLES[owner]["bg"]

            if selected is not None and selected[0] == r and selected[1] == c:
                cell.style.boxShadow = "0 0 0 2px #34d399 inset"

            if occ:
                knight_color = COLOR_STYLES[occ[0]]["ring"]
                cell.innerHTML = f'<span style="color:{knight_color}">♞</span>'

            for dr, dc, side in [(0, 1, "right"), (1, 0, "bottom")]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m.size and 0 <= nc < m.size and owner != "." and m.board[nr][nc] == owner:
                    if m.has_bridge((r, c), (nr, nc)):
                        cell.style.setProperty(f"border-{side}", f"3px solid {COLOR_STYLES[owner]['ring']}")

            cell.className = base
            cell.onclick = create_proxy(lambda evt, rr=r, cc=c: on_cell_click(rr, cc))
            container.appendChild(cell)

    update_hud()


def update_hud():
    m = current_match
    document.querySelector("#log").innerText = m.log
    document.querySelector("#phase_label").innerText = (
        "Phase 1: Maneuvers" if m.phase == 1 else "Phase 2: Battle"
    )
    b_name = m.players["B"]["name"] or "waiting..."
    w_name = m.players["W"]["name"] or "waiting..."
    document.querySelector("#black_name_label").innerText = f"Amber Throne: {b_name}"
    document.querySelector("#white_name_label").innerText = f"Cyan Throne: {w_name}"

    turn_label = document.querySelector("#turn_label")
    if m.winner:
        if m.winner == "draw":
            turn_label.innerText = "The realm is split — a draw!"
        else:
            turn_label.innerText = f"{m.players[m.winner]['name']} has won the realm!"
        turn_label.className = "text-center text-lg font-extrabold text-amber-300"
    else:
        turn_name = m.players[m.current_turn]["name"] or "???"
        whose = "Your" if m.current_turn == my_color else f"{turn_name}'s"
        step = ""
        if m.phase == 2:
            step = " — move a knight" if m.turn_step == "move" else " — build a bridge"
        turn_label.innerText = f"{whose} turn{step}"
        turn_label.className = "text-center text-lg font-extrabold text-emerald-400"


def sync_and_render():
    window.pushState(json.dumps(current_match.to_dict()))
    draw_board()


def create_initial_state(name):
    m = Match()
    m.players["B"]["name"] = name
    return json.dumps(m.to_dict())


def render_state(state_json, color, name):
    global current_match, my_color, my_name, selected
    my_color = color
    my_name = name
    selected = None
    current_match = Match.from_dict(json.loads(state_json))
    draw_board()


def init_ai_game(player_name, player_color, mode="easy"):
    """Initialize a single-player game against AI."""
    global current_match, my_color, my_name, selected, is_vs_ai, ai_color

    set_ai_mode(mode)
    my_color = player_color
    my_name = player_name
    ai_color = "W" if player_color == "B" else "B"
    is_vs_ai = True
    selected = None
    
    # Create initial state
    m = Match()
    m.players["B"]["name"] = player_name if player_color == "B" else "AI Opponent"
    m.players["W"]["name"] = player_name if player_color == "W" else "AI Opponent"
    current_match = m
    
    document.querySelector("#log").innerText = f"Practice mode: {player_name} vs AI"
    draw_board()
    
    # If AI goes first, schedule its first move
    if current_match.current_turn == ai_color:
        window.setTimeout(create_proxy(lambda: trigger_ai_turn()), 1000)


window.pyCreateInitialState = create_proxy(create_initial_state)
window.pyRenderState = create_proxy(render_state)
window.pyInitAIGame = create_proxy(init_ai_game)
window.pySetAIMode = create_proxy(set_ai_mode)
