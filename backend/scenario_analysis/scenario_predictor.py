from math import pow
import copy

from backend import db, utility
from backend.scenario_analysis import scenario_utility


# player structure {'player_id': u'U03NSJJJN', 'm_w': 7, 's_l': 0, 's_w': 21, 'm_l': 0}


def index_by_player_id(list, player_id):
    for index, item in enumerate(list):
        if item['player_id'] == player_id:
            return index


def run_theoretical_combinations(results, known_matches, unplayed_matches, player_id, top_xs, reverse, combo_limit=4096):
    combinations = int(pow(2, len(unplayed_matches)))
    if combinations > combo_limit:
        return None

    for j in range(0, combinations):
        theoretical_matches = scenario_utility.create_match_scenario(unplayed_matches, j)
        full_scenario = known_matches + theoretical_matches
        ordered_players = utility.gather_scores(full_scenario)
        for top_x in top_xs:
            top_result = scenario_utility.is_top_x_wins(ordered_players, player_id, top_x, reverse=reverse)
            if top_result < 2:
                results[top_x]['winning_scenario'] = True
                if top_result == 1:  # Means they're only in top 2 due to a 3+ way tie
                    results[top_x]['tie_scenarios'][j] = [copy.copy(x) for x in theoretical_matches]
                else:
                    results[top_x]['top_x_scenarios'][j] = [copy.copy(x) for x in theoretical_matches]
    return combinations


# 0 - Mathematically impossible
# 1 - Impossible, assuming everyone else plays their matches
# 2 - Yes, they control their destiny
# 3 - Yes, they could end up tied, but control their destiny to win the tiebreaker.
# 4 - Yes, but they don't control their destiny
# 5 - Yes, but it requires a complex tiebreaker
# 6 - They can tie for 2nd, but doesn't appear they can win the tiebreaker
# 7 - No
def can_player_make_top_x(group_matches, player_id, top_xs, reverse=False):
    results = {}
    for top_x in top_xs:
        results[top_x] = {}

    played_matches = [m for m in group_matches if m.winner_id is not None]

    players_unplayed = [copy.copy(m) for m in group_matches if m.winner_id is None and (m.player_1_id == player_id or m.player_2_id == player_id)]
    other_unplayed_matches = [copy.copy(m) for m in group_matches if m.winner_id is None and m.player_1_id != player_id and m.player_2_id != player_id]

    # Let's start by assuming they go 3-0 in their remaining matches
    for m in players_unplayed:
        m.winner_id = player_id if not reverse else [x for x in [m.player_1_id, m.player_2_id] if x != player_id][0]
        m.sets = m.sets_needed

    # Most bullish scenario, they win the rest of their matches and nobody else plays the rest of theirs
    # only bother with this one if reverse=False
    if not reverse:
        ordered_players = utility.gather_scores(played_matches + players_unplayed)
        for top_x in top_xs:
            if scenario_utility.is_top_x_wins(ordered_players, player_id, top_x, reverse=reverse) == 2:
                results[top_x]['possibility'] = 0

    for top_x in top_xs:
        results[top_x]['winning_scenario'] = False
        results[top_x]['too_many_ties'] = False
        results[top_x]['tie_scenarios'] = {}
        results[top_x]['top_x_scenarios'] = {}

    combinations = run_theoretical_combinations(results, played_matches+players_unplayed, other_unplayed_matches, player_id, top_xs, reverse)
    if combinations is None:
        return results

    # If all of these scenarios result in a top X, they control their destiny

    for top_x in top_xs:
        r = results[top_x]
        if not r['winning_scenario']:
            r['possibility'] = 1

        if len(r['top_x_scenarios']) == combinations:
            r['possibility'] = 2

        if 'possibility' in r:
            continue
        # If they end up in top x of all tie situations, then they still control their destiny
        r['potential_control_destiny'] = len(r['top_x_scenarios']) + len(r['tie_scenarios']) == combinations

        r['reduced_top_x'] = scenario_utility.reduce_scenarios(list(r['top_x_scenarios'].values()), other_unplayed_matches)
        r['reduced_ties'] = scenario_utility.reduce_scenarios(list(r['tie_scenarios'].values()), other_unplayed_matches)

        # if len(r['reduced_top_x']) < len(r['top_x_scenarios']):
        #     print('Reduced top x from {} to {}'.format(len(r['top_x_scenarios']), len(r['reduced_top_x'])))
        # if len(r['reduced_ties']) < len(r['tie_scenarios']):
        #     print('Reduced ties from {} to {}'.format(len(r['tie_scenarios']), len(r['reduced_ties'])))

        # Find matchups that only exist a certain way in the scenarios
        # for m in other_unplayed_matches:
        #     m1 = copy.copy(m)
        #     m2 = copy.copy(m)
        #     m1.winner_id = m1.player_1_id
        #     m1.sets = m1.sets_needed
        #     m2.winner_id = m2.player_2_id
        #     m2.sets = m2.sets_needed
        #
        #     m1_exists = False
        #     m2_exists = False
        #     for scenario in r['reduced_top_x']:
        #         m1_exists = m1_exists or scenario_utility.match_in_list(m1, scenario)
        #         m2_exists = m2_exists or scenario_utility.match_in_list(m2, scenario)
        #     if m1_exists and not m2_exists:
        #         print('Necessary result for top {}:'.format(top_x))
        #         print_match(m1)
        #     if m2_exists and not m1_exists:
        #         print('Necessary result for top {}:'.format(top_x))
        #         print_match(m2)

        # verify they can be in the top 2 regardless of tie breakers
        r['tie_topx_scenarios'] = []
        r['non_topx_scenarios'] = 0
        total_tie_combinations = sum([int(pow(3, len(x))) for x in r['reduced_ties']])
        if total_tie_combinations > 10000:
            r['too_many_ties'] = True
        else:
            for scenario in r['reduced_ties']:
                # We may have inconsequential matches that have been removed from the scenario. Need to recreate them for gathering scores
                consequential_match_ids = [m.id for m in scenario]
                inconsequential_matches = []
                for m in other_unplayed_matches:
                    if m.id not in consequential_match_ids:
                        new_m = copy.copy(m)
                        new_m.winner_id = new_m.player_1_id
                        new_m.sets = new_m.sets_needed
                        inconsequential_matches.append(new_m)

                # TODO Before trying to change all the scores, let's make sure they haven't already lost to everyone they're tied with

                # for each match that matters, we have 2 more score possibilities. We've already tested 3-0, but can test 3-1 and 3-2
                theoretical_matches = [copy.copy(x) for x in scenario]
                tie_scenario_combinations = int(pow(3, len(theoretical_matches)))
                for combo_index in range(0, tie_scenario_combinations):
                    combo_array = scenario_utility.build_combo_array(combo_index, 3, len(theoretical_matches))
                    for i in range(0, len(theoretical_matches)):  # 0 or 1
                        theoretical_matches[i].sets = (int(theoretical_matches[i].sets_needed/2) + 1 if theoretical_matches[i].play_all_sets else theoretical_matches[i].sets_needed) + combo_array[i]
                    full_scenario = played_matches + players_unplayed + inconsequential_matches + theoretical_matches
                    ordered_players = utility.gather_scores(full_scenario)
                    if reverse:
                        ordered_players.reverse()
                    if index_by_player_id(ordered_players, player_id) <= top_x-1:
                        r['tie_topx_scenarios'].append(theoretical_matches)
                    else:
                        r['non_topx_scenarios'] += 1

    for top_x in top_xs:
        r = results[top_x]
        if 'possibility' in r:
            continue
        if len(r['reduced_ties']) > 0 and r['non_topx_scenarios'] == 0 and r['potential_control_destiny'] and not r['too_many_ties']:
            r['possibility'] = 3
        elif len(r['reduced_top_x']) > 0:
            r['possibility'] = 4
        elif len(r['tie_topx_scenarios']) > 0:
            r['possibility'] = 5
        elif len(r['reduced_ties']) > 0:
            r['possibility'] = 6
        else:
            r['possibility'] = 7
    return results


def analyze_player_possibilities(league_name, player_id):
    all_matches = db.get_matches_for_season(league_name, db.get_current_season(league_name))
    all_players = db.get_players(league_name)
    player_matches = [x for x in all_matches if x.player_1_id == player_id or x.player_2_id == player_id]
    group = player_matches[0].grouping
    group_matches = [m for m in all_matches if m.grouping == group and m.player_1_id is not None and m.player_2_id is not None]
    num_players = len(set([x.player_1_id for x in group_matches] + [x.player_2_id for x in group_matches]))

    players_unplayed = len([copy.copy(m) for m in group_matches if m.winner_id is None and (m.player_1_id == player_id or m.player_2_id == player_id)])

    top_x_results = can_player_make_top_x(group_matches, player_id, [2, num_players - 2])
    bottom_x_results = can_player_make_top_x(group_matches, player_id, [2, num_players - 2], reverse=True)

    print('Future analysis for ' + utility.get_player_name(all_players, player_id))
    if 'possibility' not in top_x_results[2]:
        print('Too many unplayed games to be able to calculate.')
        return

    promotion = ''
    relegation = ''
    games_left = "If they win their remaining games 3-0, " if players_unplayed else "When the dust settles, "
    top_2_possibility = top_x_results[2]['possibility']
    bot_2_possibility = bottom_x_results[2]['possibility']

    if bottom_x_results[num_players-2]['possibility'] in [1, 7]:
        promotion = "Promotion is already locked in."
    elif top_2_possibility == 2:
        promotion = games_left + "they will be guaranteed promotion."
    elif top_2_possibility == 3:
        promotion = games_left + "they could end up tied, but should still receive promotion."
    elif top_2_possibility == 4:
        if top_x_results[2]['too_many_ties']:
            promotion = games_left + "they could get promoted, but there are too many tie scenarios to know for sure."
        else:
            promotion = games_left + "they could get promoted, but it depends on other games' outcomes."
        if top_x_results[num_players-2]['possibility'] in [2, 3]:
            promotion += " They will be safe from relegation though."
    elif top_2_possibility == 5:
        promotion = games_left + "they could tie for promotion, and there's at least one scenario where they win the tiebreaker."
    elif top_2_possibility == 6:
        if top_x_results[2]['too_many_ties']:
            promotion = games_left + "they could tie for promotion, but there are too many tie scenarios to know if they can win the tiebreaker."
        else:
            promotion = games_left + "they could tie for promotion, but it looks like they wouldn't be able to win the tiebreaker."
        if top_x_results[num_players-2]['possibility'] in [2, 3]:
            promotion += " They will be safe from relegation though."
    elif top_2_possibility in [0, 1, 7]:
        promotion = games_left + "they will still be out of reach of promotion."

    lose_games_left = "If they lose their remaining games 0-3, " if players_unplayed else "When the dust settles, "
    if top_x_results[num_players-2]['possibility'] in [0, 1, 7]:
        relegation = "Relegation is locked in."
    elif bot_2_possibility in [1, 7]:
        relegation = lose_games_left+"they will still be safe from relegation."
    elif bot_2_possibility == 2:
        relegation = lose_games_left+"they will be guaranteed relegation."
    elif bot_2_possibility == 3:
        relegation = lose_games_left+"they could end up tied for staying, but will lose any tiebreakers."
    elif bot_2_possibility == 4:
        if bottom_x_results[2]['too_many_ties']:
            relegation = lose_games_left + "they could get relegated, but there are too many tie scenarios to know for sure."
        else:
            relegation = lose_games_left+"they could get relegated based on the outcome of other games."
    elif bot_2_possibility == 5:
        relegation = lose_games_left+"they could tie for relegation and there's at least one scenario where they lose the tiebreaker."
    elif bot_2_possibility == 6:
        if bottom_x_results[2]['too_many_ties']:
            relegation = lose_games_left + "they could tie for relegated, but there are too many tie scenarios to know if they can win the tiebreaker."
        else:
            relegation = lose_games_left+"they could tie for relegation, but should be able to win any tiebreakers."

    print('Promotion Chances: '+promotion)
    print('Relegation Chances: '+relegation)


def get_player_names(player_ids, all_players):
    to_return = ""
    num_players = len(player_ids)
    for idx, player_id in enumerate(player_ids):
        to_return += utility.get_player_name(all_players, player_id)
        if idx < num_players - 2:
            to_return += ", "
        if idx == num_players - 2:
            to_return += " and "
    return to_return


def analyze_group_possibilities(league_name, group, num_promoted=2):
    all_matches = db.get_matches_for_season(league_name, db.get_current_season(league_name))
    all_groups = sorted(list(set([m.grouping for m in all_matches])))
    top_group = group == all_groups[0]
    no_relegations = group == all_groups[-1]
    #TODO we could get away with calculating less if we know we're in top or bottom group

    all_players = db.get_players(league_name)
    group_matches = [m for m in all_matches if m.grouping == group and m.player_1_id is not None and m.player_2_id is not None]
    unplayed_matches = [m for m in group_matches if m.winner_id is None]

    player_ids = list(set([m.player_1_id for m in group_matches] + [m.player_2_id for m in group_matches]))
    num_players = len(player_ids)
    promotion_locked = []
    promotion_destiny_controlled = []
    promotion_possible = []
    promotion_unclear = []

    relegation_locked = []
    relegation_avoidance_destiny_controlled = []
    relegation_avoidance_possible = []
    relegation_avoidance_unclear = []

    champ_locked = []
    champ_destiny_controlled = []
    champ_possible = []
    champ_unclear = []

    no_info = False
    for player_id in player_ids:
        top_x_results = can_player_make_top_x(group_matches, player_id, [num_promoted, num_players - num_promoted])
        bottom_x_results = can_player_make_top_x(group_matches, player_id, [num_promoted, num_players - num_promoted], reverse=True)
        if top_group:
            champ_results = can_player_make_top_x(group_matches, player_id, [1])
            nonchamp_results = can_player_make_top_x(group_matches, player_id, [num_players-1], reverse=True)

        if 'possibility' not in top_x_results[num_promoted]:
            no_info = True
            break
        promotion_impossible = top_x_results[num_promoted]['possibility'] in [0, 1, 7]
        promotion_impossible = promotion_impossible or (top_x_results[num_promoted]['possibility'] == 6 and not top_x_results[num_promoted]['too_many_ties'])
        if not promotion_impossible:
            if bottom_x_results[num_players - num_promoted]['possibility'] in [1, 7]:
                promotion_locked.append(player_id)
            elif bottom_x_results[num_players - num_promoted]['possibility'] in [6] and not top_x_results[num_promoted]['too_many_ties']:
                promotion_locked.append(player_id)
            elif top_x_results[num_promoted]['possibility'] in [2, 3]:
                promotion_destiny_controlled.append(player_id)
            elif top_x_results[num_promoted]['possibility'] in [4, 5] and not top_x_results[num_promoted]['too_many_ties']:
                promotion_possible.append(player_id)
            elif top_x_results[num_promoted]['too_many_ties'] and top_x_results[num_promoted]['possibility'] in [4, 6]:
                promotion_unclear.append(player_id)

        relegation_impossible = bottom_x_results[num_promoted]['possibility'] in [1, 7]
        relegation_impossible = relegation_impossible or (bottom_x_results[num_promoted]['possibility'] == 6 and not bottom_x_results[num_promoted]['too_many_ties'])
        if not relegation_impossible:
            if top_x_results[num_players - num_promoted]['possibility'] in [0, 1, 7]:
                relegation_locked.append(player_id)
            elif top_x_results[num_players - num_promoted]['possibility'] in [6] and not top_x_results[num_players - num_promoted]['too_many_ties']:
                relegation_locked.append(player_id)
            elif top_x_results[num_players - num_promoted]['possibility'] in [2, 3]:
                relegation_avoidance_destiny_controlled.append(player_id)
            elif top_x_results[num_players - num_promoted]['possibility'] in [4, 5] and not top_x_results[num_players - num_promoted]['too_many_ties']:
                relegation_avoidance_possible.append(player_id)
            elif top_x_results[num_players - num_promoted]['too_many_ties'] and top_x_results[num_players - num_promoted]['possibility'] in [4, 6]:
                relegation_avoidance_unclear.append(player_id)

        if top_group:
            champ_impossible = champ_results[1]['possibility'] in [0, 1, 7]
            champ_impossible = champ_impossible or (champ_results[1]['possibility'] == 6 and not champ_results[1]['too_many_ties'])
            if not champ_impossible:
                if nonchamp_results[num_players-1]['possibility'] in [1, 7]:
                    champ_locked.append(player_id)
                elif nonchamp_results[num_players-1]['possibility'] in [6] and not champ_results[1]['too_many_ties']:
                    champ_locked.append(player_id)
                elif champ_results[1]['possibility'] in [2, 3]:
                    champ_destiny_controlled.append(player_id)
                elif champ_results[1]['possibility'] in [4, 5] and not champ_results[1]['too_many_ties']:
                    champ_possible.append(player_id)
                elif champ_results[1]['too_many_ties'] and champ_results[1]['possibility'] in [4, 6]:
                    champ_unclear.append(player_id)

    # X and Y have promotion locked in.
    # X, Y, and Z are in the running for promotion and control their destiny.
    # X and Y could still be promoted, but it requires other games to fall a certain way.
    # X might be able to reach promotion, but there are too many tie scenarios to know for sure.
    # Promotion is out of reach for Y and Z
    promotion_message = ""
    if len(promotion_locked):
        promotion_message += get_player_names(promotion_locked, all_players)
        if len(promotion_locked) > 1:
            promotion_message += " are locked into promotion.\n"
        else:
            promotion_message += " is locked into promotion.\n"

    if len(promotion_destiny_controlled):
        promotion_message += get_player_names(promotion_destiny_controlled, all_players)
        if len(promotion_destiny_controlled) > 1:
            promotion_message += " are in the running for promotion and control their destiny.\n"
        else:
            promotion_message += " is in the running for promotion and control their destiny.\n"

    if len(promotion_possible):
        promotion_message += get_player_names(promotion_possible, all_players)
        promotion_message += " could still get promotion, but it will require others' games to fall a certain way.\n"

    if len(promotion_unclear):
        promotion_message += "It's unclear if "
        promotion_message += get_player_names(promotion_unclear, all_players)
        promotion_message += " can still achieve promotion. There are too many tiebreaker scenarios to calculate.\n"

    relegation_message = ""
    if len(relegation_avoidance_destiny_controlled):
        relegation_message += get_player_names(relegation_avoidance_destiny_controlled, all_players)
        relegation_message += " could get relegated, but they can avoid it by winning their remaining games.\n"

    if len(relegation_avoidance_possible):
        relegation_message += get_player_names(relegation_avoidance_possible, all_players)
        if len(relegation_avoidance_possible) > 1:
            relegation_message += " are"
        else:
            relegation_message += " is"
        relegation_message += " facing relegation. Even if they win out, it will require others' games to fall a certain way to avoid it.\n"

    if len(relegation_avoidance_unclear):
        relegation_message += "It's unclear if "
        relegation_message += get_player_names(relegation_avoidance_unclear, all_players)
        relegation_message += " can avoid relegation. There are too many tiebreaker scenarios to calculate.\n"

    if len(relegation_locked):
        relegation_message += get_player_names(relegation_locked, all_players)
        if len(relegation_locked) > 1:
            relegation_message += " are locked into relegation.\n"
        else:
            relegation_message += " is locked into relegation.\n"

    champ_message = ""
    if len(champ_locked):
        champ_message += get_player_names(champ_locked, all_players)
        champ_message += " is locked in as Champion!\n"

    if len(champ_destiny_controlled):
        champ_message += get_player_names(champ_destiny_controlled, all_players)
        if len(champ_destiny_controlled) > 1:
            champ_message += " are in the running for the championship and control their destiny.\n"
        else:
            champ_message += " is in the running for the championship and control their destiny.\n"

    if len(champ_possible):
        champ_message += get_player_names(champ_possible, all_players)
        champ_message += " could still claim the championship, but it will require others' games to fall a certain way.\n"

    if len(champ_unclear):
        champ_message += "It's unclear if "
        champ_message += get_player_names(champ_unclear, all_players)
        champ_message += " can still claim the championship. There are too many tiebreaker scenarios to calculate.\n"

    total_message = ""
    if top_group:
        total_message += champ_message + "\n"
    else:
        total_message += promotion_message + "\n"
    if not no_relegations:
        total_message += relegation_message

    if no_info:
        total_message = "There are too many unplayed games to analyze this group."

    final_message = "*Group {} Analysis:*\n".format(group)
    if len(unplayed_matches) > 0 and not no_info:
        final_message += "_assuming all matches get played..._\n"
    final_message += total_message
    print(final_message)
    return final_message


def analyze_player_by_name(league_name, name):
    all_players = db.get_players(league_name)
    player = [x.slack_id for x in all_players if x.name == name][0]
    analyze_player_possibilities(league_name, player)
