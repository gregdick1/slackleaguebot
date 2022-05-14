from backend import db, utility, slack_util

MISFORMAT_MSG = 'Not a group. Format is simply `Group A`'
NOT_A_GROUP_MSG = 'Not a group (or I messed up).'


def handles_message(lctx, command_object):
    if command_object.text.upper().startswith('GROUP '):
        return True
    return False


def build_message_for_group(lctx, group):
    season = db.get_current_season(lctx.league_name)
    all_matches = db.get_matches_for_season(lctx.league_name, season)
    all_players = db.get_players(lctx.league_name)
    group_matches = [m for m in all_matches if m.grouping.upper() == group]

    if not len(group_matches):
        return None

    players = utility.gather_scores(group_matches)
    message = 'Group ' + group + ':'

    for p in players:
        message += '\n' + utility.get_player_name(all_players, p['player_id']) + ' ' + str(p['m_w']) + '-' + str(p['m_l'])
        message += ' (' + str(p['s_w']) + '-' + str(p['s_l']) + ')'
    return message


def handle_message(lctx, command_object):
    text = command_object.text[6:]
    if len(text) != 1:
        slack_util.post_message(lctx, MISFORMAT_MSG, command_object.channel)
        return

    group = text[0].upper()
    message = build_message_for_group(lctx, group)
    if message is None:
        slack_util.post_message(lctx, NOT_A_GROUP_MSG, command_object.channel)
    else:
        slack_util.post_message(lctx, message, command_object.channel)
