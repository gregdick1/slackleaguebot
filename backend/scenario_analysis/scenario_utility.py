import copy


# Return one of 3 scenarios
# 0 - The player is in the top X without the need for a tiebreaker on sets
# 1 - The player is in a >3 way tie that spans the border between top X and not top X
# 2 - The player is neither
#
# If reverse=True, this essentially becomes a "is_bottom_x" method
def is_top_x_wins(ordered_players, player_id, top_x, reverse=False):
    if player_id not in [x['player_id'] for x in ordered_players]:
        return 2
    if len(ordered_players) <= top_x:
        return 0

    if reverse:
        ordered_players = ordered_players[:]
        ordered_players.reverse()

    last_high_enough_wins = ordered_players[top_x-1]['m_w']  # num wins for last person in top x
    player_wins = 0
    player_idx = 0
    num_last_high_enough_players = 0
    last_high_enough_player_idx = 0
    for idx, p in enumerate(ordered_players):
        if p['player_id'] == player_id:
            player_idx = idx
            player_wins = p['m_w']
            if (not reverse and player_wins > last_high_enough_wins) or (reverse and player_wins < last_high_enough_wins):
                return 0
        if p['m_w'] == last_high_enough_wins:
            num_last_high_enough_players += 1
            last_high_enough_player_idx = idx

    if player_idx <= top_x-1 and num_last_high_enough_players <= 2:
        return 0
    if ((not reverse and player_wins >= last_high_enough_wins) or (reverse and player_wins <= last_high_enough_wins)) and num_last_high_enough_players >= 3:
        if last_high_enough_player_idx <= top_x-1:
            return 0
        return 1
    return 2


def match_in_list(match, matches):
    for m in matches:
        if m.id == match.id and m.winner_id == match.winner_id and m.sets == match.sets:
            return True
    return False


def serialize_match(m):
    return str(m.id)+'_'+m.player_1_id+'_'+m.player_2_id+'_'+m.winner_id+'_'+str(m.sets)


def serialize_scenario(matches):
    newlist = sorted(matches, key=lambda x: x.id)
    to_return = 'scenario_'
    for m in newlist:
        to_return += serialize_match(m)+'_'
    return to_return


def scenario_sets_identical(scenario_list_1, scenario_list_2):
    if not len(scenario_list_1) == len(scenario_list_2):
        return False
    serialized_scenarios_1 = set([serialize_scenario(x) for x in scenario_list_1])
    serialized_scenarios_2 = set([serialize_scenario(x) for x in scenario_list_2])
    return serialized_scenarios_1 == serialized_scenarios_2


def reduce_scenarios(scenarios, theoretical_matches):
    for m in theoretical_matches:
        m1 = copy.copy(m)
        m2 = copy.copy(m)

        m1.winner_id = m1.player_1_id
        m1.player_1_score = m1.sets_needed
        m1.player_2_score = 0
        m1.sets = m1.sets_needed
        m1.tie_score = 0

        m2.winner_id = m2.player_2_id
        m2.player_2_score = m2.sets_needed
        m2.player_1_score = 0
        m2.sets = m2.sets_needed
        m2.tie_score = 0

        m1_scenarios = []
        m2_scenarios = []
        for scenario in scenarios:
            if match_in_list(m1, scenario):
                m1_scenarios.append([x for x in scenario if x.id != m.id])
            if match_in_list(m2, scenario):
                m2_scenarios.append([x for x in scenario if x.id != m.id])
        if scenario_sets_identical(m1_scenarios, m2_scenarios):
            return reduce_scenarios(m1_scenarios, [x for x in theoretical_matches if x.id != m.id])
    return scenarios


def build_combo_array(combo_index, base, array_size):
    j = combo_index
    combo_array = []
    while j > 0:
        q, r = divmod(j, base)
        combo_array.append(r)
        j = q
    while len(combo_array) < array_size:
        combo_array.append(0)
    return combo_array


def create_match_scenario(unplayed_matches, combo_index):
    theoretical_matches = [copy.copy(m) for m in unplayed_matches]
    combo_array = build_combo_array(combo_index, 2, len(theoretical_matches))

    for i in range(0,len(theoretical_matches)):
        m = theoretical_matches[i]
        if combo_array[i] == 0:
            m.winner_id = m.player_1_id
            m.player_1_score = m.sets_needed
            m.player_2_score = 0
        else:
            m.winner_id = m.player_2_id
            m.player_2_score = m.sets_needed
            m.player_1_score = 0
        m.sets = m.sets_needed
        m.tie_score = 0
    return theoretical_matches
