import datetime
import time
import json

from slack_sdk import WebClient

from backend import db, utility, configs, participants

users_list = []
last_get_users_date = None


def _get_slack_client(lctx):
    if lctx.slack_client is None:
        return WebClient(token=lctx.configs[configs.SLACK_API_KEY])
    else:
        return lctx.slack_client


def _get_users_list(lctx, force_query=False):
    if not globals()['users_list'] or force_query:
        response = _get_slack_client(lctx).users_list()
        all_members = response.data['members']
        while len(response.data['response_metadata']['next_cursor']) != 0:
            response = _get_slack_client(lctx).users_list(cursor=response.data['response_metadata']['next_cursor'])
            all_members = all_members + response.data['members']
        globals()['users_list'] = all_members
        globals()['last_get_users_date'] = datetime.datetime.now().isoformat()
        return all_members
    return globals()['users_list']


def post_message(lctx, message, channel):
    response = _get_slack_client(lctx).chat_postMessage(channel=channel, text=message, as_user=True)
    return response


def add_reaction(lctx, channel, timestamp, reaction):
    response = _get_slack_client(lctx).reactions_add(name=reaction, channel=channel, timestamp=timestamp)
    return response


# Good for adding a player at a time. Inefficient for many players at once
def get_slack_id(lctx, player_name):
    users = _get_users_list(lctx)
    for user in users:
        x = user['profile']['real_name']
        if user['profile']['real_name'].startswith(player_name) and not user['deleted']:
            return user['id']
    return None


def get_deactivated_slack_ids(lctx):
    users = _get_users_list(lctx)
    deactivated = [x['id'] for x in users if x['deleted']]
    players = db.get_players(lctx.league_name)
    deactivated_players = [x.slack_id for x in players if x.slack_id in deactivated]
    return deactivated_players


def send_match_message(lctx, message, to_user, against_user, players_dictionary, debug=True):
    if to_user is None:
        return ''

    r = participants.resolver(lctx.league_name)
    if against_user is None:
        message = 'This week, you have a bye. Relax and get some practice in.'
    else:
        message = message.replace("@against_user", r.tag(against_user))
        season = db.get_current_season(lctx.league_name)
        partner = r.partner_of(to_user, season)
        message = message.replace("@partner_user", '<@' + partner + '>' if partner else '')

    if debug and to_user == lctx.configs[configs.COMMISSIONER_SLACK_ID]:
        post_message(lctx, message, lctx.configs[configs.COMMISSIONER_SLACK_ID])

    debug_message = message
    if against_user is not None:
        for slack_id in r.slack_ids(against_user) + [partner]:
            if slack_id in players_dictionary:
                debug_message = debug_message.replace('<@' + slack_id + '>', '<@' + players_dictionary[slack_id] + '>')
    if debug:
        print("Debug sent to " + players_dictionary[to_user] + ": " + debug_message)
        return "Debug sent to " + players_dictionary[to_user] + ": " + debug_message

    post_message(lctx, message, to_user)
    print("For reals sent to " + players_dictionary[to_user] + ": " + debug_message)
    return "For reals sent to " + players_dictionary[to_user] + ": " + debug_message


def send_match_messages(lctx, message, cutoff_date, is_reminder, skip_matches, debug=True):
    season = db.get_current_season(lctx.league_name)
    matches = db.get_matches_for_season(lctx.league_name, season)
    players_dictionary = utility.get_players_dictionary(lctx)
    r = participants.resolver(lctx.league_name)

    sent_matches = []
    for match in matches:
        if match.id in skip_matches:
            continue
        if match.week > cutoff_date:
            continue
        if match.winner_id is not None:
            continue
        if is_reminder and (match.player_1_id is None or match.player_2_id is None):
            continue
        if not is_reminder and match.message_sent:
            continue

        for side, other in ((match.player_1_id, match.player_2_id), (match.player_2_id, match.player_1_id)):
            for recipient in (r.slack_ids(side) if side is not None else [None]):
                send_match_message(lctx, message, recipient, other, players_dictionary, debug=debug)
                time.sleep(1.5)
        sent_matches.append(match.id)
        if not is_reminder and not debug:
            db.mark_match_message_sent(lctx.league_name, match.id)

    return sent_matches


def send_custom_messages(lctx, message, debug=True):
    r = participants.resolver(lctx.league_name)
    if r.doubles:
        season = db.get_current_season(lctx.league_name)
        member_ids = {m for team_id in r.participants_for_season(season) for m in r.slack_ids(team_id)}
        players = [p for p in db.get_players(lctx.league_name) if p.slack_id in member_ids]
    else:
        players = db.get_active_players(lctx.league_name)

    if debug:
        post_message(lctx, message, lctx.configs[configs.COMMISSIONER_SLACK_ID])

    sent_messages = ""
    for player in players:
        if debug:
            sent_messages = sent_messages + "Debug sent to " + player.name + ": " + message + "\n"
        else:
            post_message(lctx, message, player.slack_id)
            sent_messages = sent_messages + "For reals sent to " + player.name + ": " + message + "\n"

        time.sleep(1.5)

    return sent_messages
