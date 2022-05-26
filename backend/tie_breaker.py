# player structure {'player_id': u'U03NSJJJN', 'm_w': 7, 's_l': 0, 's_w': 21, 'm_l': 0}

def get_tied_players(players):
    tied_groups = []
    for i in range(0, len(players)):
        temp = [p for p in players if p['m_w'] == i]
        if len(temp) > 0:
            tied_groups.append(temp)
    return tied_groups


def _check_more_of_player_attribute(players, attribute):
    temp = sorted(players, key=lambda x: x[attribute], reverse=True)
    if temp[0][attribute] > temp[1][attribute]:
        return temp[0]
    return None


def _check_less_of_player_attribute(players, attribute):
    temp = sorted(players, key=lambda x: x[attribute])
    if temp[0][attribute] < temp[1][attribute]:
        return temp[0]
    return None


def check_h2h_won_all(players, group_matches):
    player_ids = [p['player_id'] for p in players]
    applicable_matches = [m for m in group_matches if m.player_1_id in player_ids and m.player_2_id in player_ids]
    for player in players:
        if len([m for m in applicable_matches if m.winner_id == player['player_id']]) == len(players)-1:
            return player
    return None


def check_h2h_lost_all(players, group_matches):
    player_ids = [p['player_id'] for p in players]
    applicable_matches = [m for m in group_matches if m.player_1_id in player_ids and m.player_2_id in player_ids]
    for player in players:
        player_matches = [m for m in applicable_matches if m.player_1_id == player['player_id'] or m.player_2_id == player['player_id']]
        if len([m for m in player_matches if m.winner_id is None]):
            continue
        if len([m for m in applicable_matches if m.winner_id == player['player_id']]) == 0:
            return player
    return None


def check_more_sets_won(players):
    return _check_more_of_player_attribute(players, 's_w')


def check_less_sets_won(players):
    return _check_less_of_player_attribute(players, 's_w')


def check_more_sets_lost(players):
    return _check_more_of_player_attribute(players, 's_l')


def check_less_sets_lost(players):
    return _check_less_of_player_attribute(players, 's_l')


def resolve_group_tie(players, group_matches):
    tied_players = players[:]
    moved_up = []
    # will have to reverse this one when putting the two together
    moved_down = []
    while len(tied_players) > 1:
        move_up = check_h2h_won_all(tied_players, group_matches)
        if move_up:
            moved_up.append(move_up)
            tied_players.remove(move_up)
            continue

        move_down = check_h2h_lost_all(tied_players, group_matches)
        if move_down:
            moved_down.append(move_down)
            tied_players.remove(move_down)
            continue

        move_up = check_more_sets_won(tied_players)
        if move_up:
            moved_up.append(move_up)
            tied_players.remove(move_up)
            continue

        move_down = check_less_sets_won(tied_players)
        if move_down:
            moved_down.append(move_down)
            tied_players.remove(move_down)
            continue

        move_up = check_less_sets_lost(tied_players)
        if move_up:
            moved_up.append(move_up)
            tied_players.remove(move_up)
            continue

        move_down = check_more_sets_lost(tied_players)
        if move_down:
            moved_down.append(move_down)
            tied_players.remove(move_down)
            continue

        # just take whoever
        move_up = tied_players[0]
        moved_up.append(move_up)
        tied_players.remove(move_up)
    moved_down.reverse()
    return moved_up + tied_players + moved_down


def order_players(group_players, group_matches):
    final_order = []
    max_wins = max([p['m_w'] for p in group_players])
    max_losses = max([p['m_l'] for p in group_players])
    for wins in range(max_wins, -1, -1):
        for losses in range(max_losses, -1, -1):
            temp = [p for p in group_players if p['m_w'] == wins and p['m_l'] == losses]
            final_order = final_order + resolve_group_tie(temp, group_matches)
    return final_order
