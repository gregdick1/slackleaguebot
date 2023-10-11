from backend import slack_util, configs, db
import collections

matches_or_sets_options = ['MATCHES', 'SETS']
sortby_options = ['PLAYED', 'WON', 'WINRATE']
all_valid_options = ['ALL'] + matches_or_sets_options + sortby_options
BAD_OPTION_MSG = 'The only options I recognize are `matches`, `sets`, `played`, `won`, `winrate`, and `all`.'


def handles_message(lctx, command_object):
    if command_object.text.upper().startswith('LEADERBOARD'):
        return True
    return False


def handle_message(lctx, command_object):
    text = command_object.text
    options_text = ''
    if len(text) > 11:
        options_text = text[11:].strip().upper()
    options = options_text.split(' ')
    if len(options_text) and len([x for x in options if x not in all_valid_options]):
        slack_util.post_message(lctx, BAD_OPTION_MSG, command_object.channel)
        return

    matches_or_sets_o = [x for x in options if x in matches_or_sets_options]
    if len(matches_or_sets_o) != 1:
        matches_or_sets = 'MATCHES'
    else:
        matches_or_sets = matches_or_sets_o[0]

    sortby_o = [x for x in options if x in sortby_options]
    if len(sortby_o) != 1:
        sortby = 'WON'
    else:
        sortby = sortby_o[0]

    active_only = 'ALL' not in options

    sorted_winrates = get_leaderboard(lctx, matches_or_sets, sortby, active_only)
    message = build_post(sorted_winrates, matches_or_sets, sortby)
    slack_util.post_message(lctx, message, command_object.channel)


def build_post(sorted_winrates, matches_or_sets, sortby):
    final_sort_prefix = 'matches_' if matches_or_sets.upper() == 'MATCHES' else 'games_'
    message = ''
    for player_name in list(sorted_winrates)[:10]:
        player_object = sorted_winrates[player_name]

        if sortby.upper() == 'WON':
            message += "\n {}: {}".format(player_name, player_object[final_sort_prefix+'won'])
        elif sortby.upper() == 'PLAYED':
            message += "\n {}: {}".format(player_name, player_object[final_sort_prefix+'total'])
        elif sortby.upper() == 'WINRATE':
            message += "\n {}: {}-{} {}%".format(player_name, player_object[final_sort_prefix+'won'], player_object[final_sort_prefix+'lost'], player_object[final_sort_prefix+'winrate'])
    return message


def get_leaderboard(lctx, matches_or_sets, sortby, active_only, reverse_order=True):
    final_sortby = ''
    final_sort_prefix = 'matches_' if matches_or_sets.upper() == 'MATCHES' else 'games_'
    if sortby.upper() == 'WON':
        final_sortby = final_sort_prefix+'won'
    elif sortby.upper() == 'PLAYED':
        final_sortby = final_sort_prefix+'total'
    elif sortby.upper() == 'WINRATE':
        final_sortby = final_sort_prefix+'winrate'

    matches = db.get_matches(lctx.league_name)
    players = db.get_players(lctx.league_name)

    player_dict = dict()

    for player in players:
        player_dict[player.slack_id] = {
            'matches_won': 0,
            'matches_total': 0,
            'games_won': 0,
            'games_total': 0,
            'name': player.name,
            'is_active': player.active
        }

    for match in matches:
        games_played = match.sets

        if match.player_1_id is None or match.player_2_id is None:
            continue
        if match.winner_id is None:
            continue

        player_1 = player_dict[match.player_1_id]
        player_2 = player_dict[match.player_2_id]

        player_dict[match.player_1_id]['games_total'] = player_1['games_total'] + games_played
        player_dict[match.player_2_id]['games_total'] = player_2['games_total'] + games_played
        player_dict[match.player_1_id]['matches_total'] = player_1['matches_total'] + 1
        player_dict[match.player_2_id]['matches_total'] = player_2['matches_total'] + 1

        if match.player_1_id == match.winner_id:
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets if match.play_all_sets else match.sets_needed
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets_needed - match.sets if match.play_all_sets else match.sets - match.sets_needed
            player_dict[match.player_1_id]['matches_won'] = player_1['matches_won'] + 1

        elif match.player_2_id == match.winner_id:
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets if match.play_all_sets else match.sets_needed
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets_needed - match.sets if match.play_all_sets else match.sets - match.sets_needed
            player_dict[match.player_2_id]['matches_won'] = player_2['matches_won'] + 1

    winrate_dict = dict()
    for player_id, player in player_dict.items():
        if sortby.upper() == 'WINRATE' and player['matches_total'] < 20:
            continue
        if active_only and player['is_active'] != 1:
            continue
        if player['games_total'] == 0:
            winrate_dict[player['name']] = {
                'matches_won': 0,
                'matches_lost': 0,
                'matches_total': 0,
                'games_won': 0,
                'games_lost': 0,
                'games_total': 0,
                'matches_winrate': round(0, 2),
                'games_winrate': round(0, 2)
            }
        else:
            winrate_dict[player['name']] = {
                'matches_won': player['matches_won'],
                'matches_lost': player['matches_total'] - player['matches_won'],
                'matches_total': player['matches_total'],
                'matches_winrate': round((player['matches_won'] / player['matches_total']) * 100, 2),
                'games_won': player['games_won'],
                'games_lost': player['games_total'] - player['games_won'],
                'games_total': player['games_total'],
                'games_winrate': round((player['games_won'] / player['games_total']) * 100, 2)
            }

    sorted_winrates = collections.OrderedDict(sorted(winrate_dict.items(), key=lambda x: x[1][final_sortby], reverse=reverse_order))
    return sorted_winrates
