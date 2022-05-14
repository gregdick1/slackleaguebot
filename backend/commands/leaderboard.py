from backend import slack_util, configs, db
import collections

winrate_options = ['MATCHES', 'SETS', 'WINRATE']
BAD_OPTION_MSG = 'The only valid options are `matches`, `sets`, or `winrate`.'


def handles_message(lctx, command_object):
    if command_object.text.upper().startswith('LEADERBOARD'):
        return True
    return False


def handle_message(lctx, command_object):
    text = command_object.text
    option = ''
    if len(text) > 11:
        option = text[11:].strip().upper()
    if len(option) and option not in winrate_options:
        slack_util.post_message(lctx, BAD_OPTION_MSG, command_object.channel)
        return

    sorted_winrates = get_leaderboard(lctx, option)
    message = build_post(sorted_winrates)
    slack_util.post_message(lctx, message, command_object.channel)


def build_post(sorted_winrates):
    message = ''
    for player_name in list(sorted_winrates)[:10]:
        player_object = sorted_winrates[player_name]
        message = message + "\n {}: {}-{} ({}-{}) {}%".format(player_name, player_object['matches_won'], player_object['matches_lost'], player_object['games_won'], player_object['games_lost'], player_object['winrate'])
    return message


def get_leaderboard(lctx, sortby, reverse_order=True):
    if sortby.upper() == 'MATCHES' or sortby == '':
        sortby = 'matches_won'
    if sortby.upper() == 'SETS':
        sortby = 'games_won'
    if sortby.upper() == 'WINRATE':
        sortby = 'winrate'

    matches = db.get_matches(lctx.league_name)
    players = db.get_players(lctx.league_name)

    player_dict = dict()

    for player in players:
        player_dict[player.slack_id] = {
            'matches_won': 0,
            'matches_total': 0,
            'games_won': 0,
            'games_total': 0,
            'name': player.name
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
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets_needed
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets-match.sets_needed
            player_dict[match.player_1_id]['matches_won'] = player_1['matches_won'] + 1

        elif match.player_2_id == match.winner_id:
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets_needed
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets - match.sets_needed
            player_dict[match.player_2_id]['matches_won'] = player_2['matches_won'] + 1

    winrate_dict = dict()
    for player_id, player in player_dict.items():
        if sortby == 'winrate' and player['matches_total'] < 20:
            continue
        if player['games_total'] == 0:
            winrate_dict[player['name']] = {
                'matches_won': 0,
                'matches_lost': 0,
                'games_won': 0,
                'games_lost': 0,
                'winrate': round(0, 2)
            }
        else:
            winrate_dict[player['name']] = {
                'matches_won': player['matches_won'],
                'matches_lost': player['matches_total'] - player['matches_won'],
                'games_won': player['games_won'],
                'games_lost': player['games_total'] - player['games_won'],
                'winrate': round((player['games_won'] / player['games_total']) * 100, 2)
            }

    sorted_winrates = collections.OrderedDict(sorted(winrate_dict.items(), key=lambda x: x[1][sortby], reverse=reverse_order))
    return sorted_winrates
