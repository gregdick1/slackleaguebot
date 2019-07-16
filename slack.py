from slacker import Slacker
import db
import time, datetime, bot_config

slack_client = Slacker(bot_config.get_slack_api_key())


def send_reminder(to_user, against_user, debug=True):
    if to_user is None or against_user is None:
        return
    message = 'Friendly reminder that you have a match against <@'+against_user+'>. Please work with them to find a time to play.'
    if debug:
        print('Sending to', to_user, ':', message)
    else:
        slack_client.chat.post_message(to_user, message, as_user=True)
        print('For reals sent to', to_user, ':', message)
    time.sleep(1.5)

def send_message(to_user, against_user, debug=True):
    if to_user is None:
        return
    message = 'This week, you have a bye. Relax and get some practice in.'
    if against_user is not None:
        message = 'This week, you play against <@'+against_user+'>. Please message them _today_ to find a time that works. After your match, report the winner and # of sets (best of 3) to <@UGP9FEBLY> in <#C03NHDHBD>.'
    if debug and not to_user == bot_config.get_commissioner_slack_id():
        print('Sending to', to_user, ':', message)
    else:
        slack_client.chat.post_message(to_user, message, as_user=True)
        print('For reals sent to', to_user, ':', message)
    time.sleep(1.5)

def send_messages_for_week(week, debug=True):
    matches = db.get_matches_for_week(week)
    for match in matches:
        if match.winner_id is None:
            send_message(match.player_1_id, match.player_2_id, debug=debug)
            send_message(match.player_2_id, match.player_1_id, debug=debug)

def send_reminders_for_week(week, debug=True):
    matches = db.get_matches_for_week(week)
    for match in matches:
        if match.winner_id is None:
            send_reminder(match.player_1_id, match.player_2_id, debug=debug)
            send_reminder(match.player_2_id, match.player_1_id, debug=debug)

def send_custom_to_active(message, debug=True):
    players = db.get_active_players()

    if debug:
        slack_client.chat.post_message(bot_config.get_commissioner_slack_id(), message, as_user=True)

    return_message = ""
    for player in players:
        if debug:
            return_message = return_message + f"Debug sending to {player.name}: {message} \n"
        else:
            slack_client.chat.post_message(player.slack_id, message, as_user=True)
            return_message = return_message + f"For reals sending to {player.name}: {message} \n"
        time.sleep(1.5)
    
    return return_message

def send_custom_for_missed_games(message, num_missed, week, debug=True):
    season = db.get_current_season()
    season_matches = db.get_matches_for_season(season)
    players = {}
    for match in season_matches:
        if match.week <= week and match.winner_id is None:
            if match.player_1_id not in players:
                players[match.player_1_id] = set()
            if match.player_2_id not in players:
                players[match.player_2_id] = set()

            players[match.player_1_id].add(match.week)
            players[match.player_2_id].add(match.week)

    for player_id in players:
        test = len(players[player_id])
        if len(players[player_id]) >= num_missed:
            if debug and not player_id == bot_config.get_commissioner_slack_id():
                print('Sending to', player_id, ':', message)
            else:
                slack_client.chat.post_message(player_id, message, as_user=True)
                print('For reals sent to', player_id, ':', message)
            time.sleep(1.5)
