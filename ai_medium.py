import random
import json

def evaluate_board_position_medium(m, color):
    enemy = "W" if color == "B" else "B"

    ringforts = sum(
        1 for r in range(m.size)
        for c in range(m.size)
        if m.board[r][c] == color
    )

    enemy_ringforts = sum(
        1 for r in range(m.size)
        for c in range(m.size)
        if m.board[r][c] == enemy
    )

    my_knights = len(m.players[color]["knights"])
    enemy_knights = len(m.players[enemy]["knights"])

    my_kingdoms = m.count_kingdoms(color)
    enemy_kingdoms = m.count_kingdoms(enemy)

    return (
        ringforts * 12 +
        my_knights * 60 -
        enemy_knights * 65 -
        my_kingdoms * 8 +
        enemy_kingdoms * 10 -
        enemy_ringforts * 8
    )

def score_move_medium(m, color, move):
    """1-ply lookahead scoring (cheap but strong)."""
    m2 = simulate_match_state_medium(m)

    # Apply move (simplified but safe)
    if len(move) == 3:
        idx, r, c = move
        m2.players[color]["knights"][idx] = [r, c]
        m2.board[r][c] = color
    else:
        a, b = move
        m2.bridges.append([list(a), list(b)])

    return evaluate_board_position_medium(m2, color)

def ai_choose_phase1_move_medium(m, ai_color):
    legal_moves = m.legal_phase1_moves_for(ai_color)
    if not legal_moves:
        return None

    best_move = None
    best_score = -999

    for move in legal_moves:
        idx, r, c = move

        base_score = score_move_medium(m, ai_color, move)

        # center bias (keep your style)
        center_penalty = abs(r - 4) + abs(c - 4)

        # slight expansion bonus
        pos = m.players[ai_color]["knights"][idx]
        expand_bonus = abs(r - pos[0]) + abs(c - pos[1])

        score = base_score - center_penalty * 0.3 + expand_bonus * 1.5

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def ai_choose_phase2_move_medium(m, ai_color):
    legal_moves = m.legal_phase2_knight_moves_for(ai_color)
    if not legal_moves:
        return None

    enemy = "W" if ai_color == "B" else "B"

    capture, claim, other = [], [], []

    for move in legal_moves:
        idx, r, c = move
        occupant = m.knight_at(r, c)

        score = score_move_medium(m, ai_color, move)

        # lookahead bonus: “what if opponent responds?”
        m2 = simulate_match_state_medium(m)
        m2.players[ai_color]["knights"][idx] = [r, c]
        m2.board[r][c] = ai_color

        enemy_moves = m2.legal_phase2_knight_moves_for(enemy)
        enemy_pressure = 0

        for em in enemy_moves[:5]:  # limit cost
            e_idx, er, ec = em
            enemy_pressure = max(enemy_pressure, score_move_medium(m2, enemy, em))

        score -= enemy_pressure * 0.3

        if occupant and occupant[0] == enemy:
            capture.append((move, score + 200))
        elif m.board[r][c] == enemy:
            claim.append((move, score + 100))
        else:
            other.append((move, score))

    pool = capture or claim or other
    return max(pool, key=lambda x: x[1])[0]


def ai_choose_phase2_bridge_medium(m, ai_color):
    legal_pairs = m.legal_bridge_pairs_for(ai_color)
    if not legal_pairs:
        return None

    best_pair = None
    best_score = -999

    for a, b in legal_pairs:
        m2 = simulate_match_state_medium(m)
        m2.bridges.append([list(a), list(b)])

        before = m.count_kingdoms(ai_color)
        after = m2.count_kingdoms(ai_color)

        score = (before - after) * 120  # stronger merge value

        # bonus: central bridges matter more
        ar, ac = a
        br, bc = b
        center_bonus = (8 - (abs(ar-4)+abs(ac-4))) * 0.5

        score += center_bonus

        if score > best_score:
            best_score = score
            best_pair = (a, b)

    return best_pair


def ai_take_turn_medium(m, ai_color):
    """
    Execute a full AI turn: move a knight and (in phase 2) build a bridge.
    Modifies match state in place.
    Returns True if a move was made, False if no legal moves.
    """
    if m.phase == 1:
        move = ai_choose_phase1_move_medium(m, ai_color)
        if not move:
            return False
        
        knight_idx, target_r, target_c = move
        m.players[ai_color]["knights"][knight_idx] = [target_r, target_c]
        m.board[target_r][target_c] = ai_color
        m.log = f"AI ({m.players[ai_color]['name']}) advances a knight to claim new ground."
        
        # Advance turn (inline logic - can't import from game_engine in PyScript)
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
        
        return True
    
    else:  # Phase 2
        # Move first
        move = ai_choose_phase2_move_medium(m, ai_color)
        if not move:
            return False
        
        knight_idx, target_r, target_c = move
        occupant = m.knight_at(target_r, target_c)
        captured_knight = occupant
        captured_fort = m.board[target_r][target_c] == ("W" if ai_color == "B" else "B")
        
        m.players[ai_color]["knights"][knight_idx] = [target_r, target_c]
        m.board[target_r][target_c] = ai_color
        
        msgs = [f"AI ({m.players[ai_color]['name']}) marches a knight forward."]
        if captured_knight:
            ecolor, eidx = captured_knight
            del m.players[ecolor]["knights"][eidx]
            msgs.append("An enemy knight is captured!")
            if not m.players[ecolor]["knights"]:
                m.winner = ai_color
                msgs.append(f"AI has eliminated all enemy knights and wins!")
        elif captured_fort:
            msgs.append("An enemy ringfort falls under new banners.")
        
        m.log = " ".join(msgs)
        
        if not m.winner:
            m.turn_step = "bridge"
            bridge = ai_choose_phase2_bridge_medium(m, ai_color)
            if bridge:
                cell_a, cell_b = bridge
                m.bridges.append([list(cell_a), list(cell_b)])
                m.log = f"AI builds a bridge, uniting their kingdom."
            
            # End turn and check for game end (inline logic)
            m.turn_step = "move"
            mover = m.current_turn
            other = "W" if mover == "B" else "B"
            if has_any_action(m, other):
                m.current_turn = other
            elif has_any_action(m, mover):
                m.log += f" {m.players[other]['name']} has no legal actions and passes."
            else:
                # Finalize game
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
        
        return True


def simulate_match_state_medium(m):
    """
    Create a deep copy of the match state for lookahead evaluation.
    """
    import copy
    m_copy = copy.deepcopy(m)
    return m_copy
