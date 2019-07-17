import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

import match_making
import db
from math import pow
from copy import copy

# player structure {'player_id': u'U03NSJJJN', 'm_w': 7, 's_l': 0, 's_w': 21, 'm_l': 0}

#each unplayed match has 6 potential outcomes
def apply_combo(match, combo):
    if combo < 3:
        match.winner_id = match.player_1_id
        match.sets = 5 - combo
    else:
        match.winner_id = match.player_2_id
        match.sets = 5 - (combo - 3)

def apply_binary_combo(match, combo):
    match.sets = 3
    if combo == 0:
        match.winner_id = match.player_1_id
    else:
        match.winner_id = match.player_2_id

def create_match_scenario(unplayed_matches, combo_index):
    theoretical_matches = [copy(m) for m in unplayed_matches]
    for i in range(0,len(theoretical_matches)):
        binary_place = long(pow(2, i+1)) #2, 4, 8, etc
        combo = (combo_index % binary_place) / binary_place
        m = theoretical_matches[i]
        apply_binary_combo(m, combo)
    return theoretical_matches

def index_by_player_id(list, player_id):
    for index, item in enumerate(list):
        if item['player_id'] == player_id:
            return index

def run_match_combinations(group_matches):
    player_ids = list(set([m.player_1_id for m in group_matches] + [m.player_2_id for m in group_matches]))
    played_matches = [m for m in group_matches if m.winner_id is not None]
    unplayed_matches = [copy(m) for m in group_matches if m.winner_id is None]
    #focus on each match, one at a time to see if it has implications for anyone
    for match in unplayed_matches:
        player_outcomes = {}
        for i in range(0, 6):
            player_outcomes[str(i)] = {}
            for player_id in player_ids:
                player_outcomes[str(i)][player_id] = []
            apply_combo(match, i)

            unplayed_matches_copy = [m for m in unplayed_matches if m != match]
            combinations = long(pow(2, len(unplayed_matches_copy)))
            for j in range(0, combinations):
                theoretical_matches = create_match_scenario(unplayed_matches_copy, j)
                full_scenario = played_matches + [match] + theoretical_matches
                ordered_players = match_making.gather_scores(full_scenario)
                for player_id in player_ids:
                    player_outcomes[str(i)][player_id].append(index_by_player_id(ordered_players, player_id))

        a=0

all_matches = db.get_matches_for_season(db.get_current_season())
group_matches = [m for m in all_matches if m.grouping == 'B']
run_match_combinations(group_matches)