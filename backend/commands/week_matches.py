import datetime

from backend import slack_util, db, utility, configs, participants

whole_week = 'MATCHES FOR WEEK'
user_week = 'WHO DO I PLAY'


def handles_message(lctx, command_object):
    if lctx.configs[configs.ENABLE_COMMAND_WEEK_MATCHES] == 'FALSE':
        return False

    if command_object.text.upper() == whole_week:
        return True
    if command_object.text.upper() == user_week and command_object.is_dm():
        return True
    return False


def build_whole_week_message(matches, players):
    message = ""
    for match in matches:
        message = message + f"\n {utility.get_player_name(players, match.player_1_id)} vs. {utility.get_player_name(players, match.player_2_id)} : week: {match.week}"
    return message


def build_user_week_message(matches, players, user_id):
    user_match_dict = dict()
    for match in matches:
        if match.player_1_id == user_id:
            user_match_dict[utility.get_player_name(players, match.player_2_id)] = match.week
        elif match.player_2_id == user_id:
            user_match_dict[utility.get_player_name(players, match.player_1_id)] = match.week

    message = ""
    for player, week in user_match_dict.items():
        message = message + f"\n Playing: {player} | week: {week}"
    return message


def handle_message(lctx, command_object):
    timestamp = float(command_object.timestamp)
    user_date = datetime.datetime.fromtimestamp(timestamp).date()

    all_weekly_matches = db.get_matches_for_week(lctx.league_name, user_date)
    r = participants.resolver(lctx.league_name)
    names = r.names_map()

    # TODO pretty sure this fails for any day other than mondays
    if command_object.text.upper() == whole_week:
        message = build_whole_week_message(all_weekly_matches, names)
        slack_util.post_message(lctx, message, command_object.channel)
        return
    if command_object.text.upper() == user_week:
        season = db.get_current_season(lctx.league_name)
        me = r.participant_for_user(command_object.user, season) or command_object.user
        message = build_user_week_message(all_weekly_matches, names, me)
        slack_util.post_message(lctx, message, command_object.channel)
        return
