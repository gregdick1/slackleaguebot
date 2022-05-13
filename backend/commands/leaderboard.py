from backend import slack_util, configs, db
import collections


def handles_message(lctx, command_object):
    if command_object.text.upper() == 'LEADERBOARD':
        return True
    return False


def handle_message(lctx, command_object):
    sorted_winrates = get_leaderboard(lctx)
    message = build_post(sorted_winrates)
    slack_util.post_message(lctx, message, command_object.channel)


def build_post(sorted_winrates):
    message = ''
    for player_name in list(sorted_winrates)[:10]:
        player_object = sorted_winrates[player_name]
        message = message + f"\n {player_name}: {player_object['winrate']}% ({player_object['games_won']}-{player_object['games_lost']})"
    return message


def get_leaderboard(lctx, reverse_order=True):
    matches = db.get_matches(lctx.league_name)
    players = db.get_players(lctx.league_name)

    player_dict = dict()

    for player in players:
        player_dict[player.slack_id] = {
            'games_won': 0,
            'games_total': 0,
            'name': player.name
        }

    for match in matches:
        games_played = match.sets

        if match.player_1_id is None or match.player_2_id is None:
            continue

        player_1 = player_dict[match.player_1_id]
        player_2 = player_dict[match.player_2_id]

        player_dict[match.player_1_id]['games_total'] = player_1['games_total'] + games_played
        player_dict[match.player_2_id]['games_total'] = player_2['games_total'] + games_played

        if match.player_1_id == match.winner_id:
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets_needed
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets-match.sets_needed

        elif match.player_2_id == match.winner_id:
            player_dict[match.player_2_id]['games_won'] = player_2['games_won'] + match.sets_needed
            player_dict[match.player_1_id]['games_won'] = player_1['games_won'] + match.sets - match.sets_needed

    winrate_dict = dict()
    for player_id, player in player_dict.items():
        if player['games_total'] == 0:
            winrate_dict[player['name']] = {
                'games_won': 0,
                'games_lost': 0,
                'winrate': round(0, 2)
            }
        else:
            winrate_dict[player['name']] = {
                'games_won': player['games_won'],
                'games_lost': player['games_total'] - player['games_won'],
                'winrate': round((player['games_won'] / player['games_total']) * 100, 2)
            }

    sorted_winrates = collections.OrderedDict(sorted(winrate_dict.items(), key=lambda x: x[1]['winrate'], reverse=reverse_order))
    return sorted_winrates
