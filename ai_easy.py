import random
import json

def evaluate_board_position_easy(m, color):
    """Score a board position for a given color. Higher = better for that color."""
    score = 0
    
    # Count ringforts claimed
    ringforts = sum(1 for r in range(m.size) for c in range(m.size) if m.board[r][c] == color)
    score += ringforts * 10
    
    # Count knights remaining
    knights_count = len(m.players[color]["knights"])
    score += knights_count * 50
    
    # Count kingdoms (fewer is better for endgame, but for midgame we want connected territory)
    kingdoms = m.count_kingdoms(color)
    score -= kingdoms * 5
    
    return score


def ai_choose_phase1_move_easy(m, ai_color):
    """
    Phase 1: Choose a knight move that claims a ringfort.
    Prefer moves that claim more territory and avoid isolation.
    """
    legal_moves = m.legal_phase1_moves_for(ai_color)
    
    if not legal_moves:
        return None
    
    # Score each move by what it accomplishes
    best_move = None
    best_score = -999
    
    for knight_idx, target_r, target_c in legal_moves:
        # Simulate the move
        m_copy = simulate_match_state_easy(m)
        pos = m_copy.players[ai_color]["knights"][knight_idx]
        m_copy.players[ai_color]["knights"][knight_idx] = [target_r, target_c]
        m_copy.board[target_r][target_c] = ai_color
        
        # Evaluate the resulting position
        move_score = evaluate_board_position_easy(m_copy, ai_color)
        
        # Slight preference for moves near the center or toward opponent
        distance_from_center = abs(target_r - 4) + abs(target_c - 4)
        move_score -= distance_from_center * 0.5
        
        # Prefer moves that expand outward
        move_score += abs(target_r - pos[0]) * 2
        move_score += abs(target_c - pos[1]) * 2
        
        if move_score > best_score:
            best_score = move_score
            best_move = (knight_idx, target_r, target_c)
    
    return best_move


def ai_choose_phase2_move_easy(m, ai_color):
    """
    Phase 2: Choose a knight move that attacks or expands territory.
    Prioritize capturing enemy knights, then capturing ringforts, then moving to unclaimed land.
    """
    legal_moves = m.legal_phase2_knight_moves_for(ai_color)
    
    if not legal_moves:
        return None
    
    # Categorize moves
    capture_moves = []
    claim_moves = []
    other_moves = []
    
    enemy = "W" if ai_color == "B" else "B"
    
    for knight_idx, target_r, target_c in legal_moves:
        occupant = m.knight_at(target_r, target_c)
        if occupant and occupant[0] == enemy:
            # Capturing an enemy knight
            capture_moves.append((knight_idx, target_r, target_c, 100))
        elif m.board[target_r][target_c] == enemy:
            # Capturing an enemy ringfort
            claim_moves.append((knight_idx, target_r, target_c, 50))
        else:
            # Moving to empty space
            other_moves.append((knight_idx, target_r, target_c, 0))
    
    # Pick from highest priority category
    if capture_moves:
        # Prioritize capturing enemy knights, random if tie
        best = max(capture_moves, key=lambda x: x[3])
        return (best[0], best[1], best[2])
    elif claim_moves:
        best = max(claim_moves, key=lambda x: x[3])
        return (best[0], best[1], best[2])
    elif other_moves:
        # Random move for expansion (or could score by position)
        return random.choice(other_moves)[:3]
    
    return None


def ai_choose_phase2_bridge_easy(m, ai_color):
    """
    Phase 2: Choose a bridge to build between adjacent own ringforts.
    Prefer bridges that connect separate kingdoms.
    """
    legal_pairs = m.legal_bridge_pairs_for(ai_color)
    
    if not legal_pairs:
        return None
    
    # Simple heuristic: prefer bridges that merge kingdoms
    best_pair = None
    best_score = -999
    
    for cell_a, cell_b in legal_pairs:
        # Simulate building the bridge
        m_copy = simulate_match_state_easy(m)
        m_copy.bridges.append([list(cell_a), list(cell_b)])
        
        # Count kingdoms after bridge
        kingdoms_before = m.count_kingdoms(ai_color)
        kingdoms_after = m_copy.count_kingdoms(ai_color)
        
        # Score: building bridges is good, merging kingdoms is better
        merge_score = (kingdoms_before - kingdoms_after) * 100
        merge_score += 10  # Base score for building any bridge
        
        if merge_score > best_score:
            best_score = merge_score
            best_pair = (cell_a, cell_b)
    
    return best_pair


def ai_take_turn_easy(m, ai_color):
    """
    Execute a full AI turn: move a knight and (in phase 2) build a bridge.
    Modifies match state in place.
    Returns True if a move was made, False if no legal moves.
    """
    if m.phase == 1:
        move = ai_choose_phase1_move_easy(m, ai_color)
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
        move = ai_choose_phase2_move_easy(m, ai_color)
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
            bridge = ai_choose_phase2_bridge_easy(m, ai_color)
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


def simulate_match_state_easy(m):
    """
    Create a deep copy of the match state for lookahead evaluation.
    """
    import copy
    m_copy = copy.deepcopy(m)
    return m_copy
