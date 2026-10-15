import re

from backend import slack_util, configs, db, participants
from backend.commands import group

BLOCK_NEW_SCORES_MSG = "Sorry, not accepting any scores at this time."
PLAYED_YOURSELF_MSG = "You can't play against yourself."
NO_MATCH_MSG = "I couldn't find a match between you two."
WORKED_REACTION = "white_check_mark"
NOT_WORKED_REACTION = "x"
NOT_ON_TEAM_MSG = "<@{}> isn't on a team this season."
SPLIT_SIDE_MSG = "<@{}> and <@{}> aren't on the same team."
YOUR_PARTNER_MSG = "<@{}> is your partner."
SAME_TEAM_MSG = "<@{}> and <@{}> are on the same team."

TAG_RE = re.compile(r'<@([^>|\s]+)(?:\|[^>]*)?>')


def split_sides(text):
    idx = text.lower().find(' over ')
    if idx == -1:
        return None
    return text[:idx], text[idx + len(' over '):]


def _tokens(side_text):
    spaced = TAG_RE.sub(lambda m: ' <@{}> '.format(m.group(1)), side_text)
    return [t for t in re.split(r'[\s,&]+', spaced) if t]


def mentions_me(side_text):
    return any(token.lower() == 'me' for token in _tokens(side_text))


def side_ids(side_text, sender):
    ids = []
    for token in _tokens(side_text):
        tag = TAG_RE.fullmatch(token)
        if tag:
            uid = tag.group(1)
        elif token.lower() == 'me':
            uid = sender
        else:
            continue
        if uid not in ids:
            ids.append(uid)
    return ids


def parse_sides(text, sender):
    sides = split_sides(text)
    if sides is None:
        return None
    # Normalize tag labels before cutting so a label containing '-' (e.g. <@U|mary-kate>)
    # does not trip the score detector. Then cut at the first score to ignore trailing
    # mentions like "gg @them" or "thanks @partner".
    right = TAG_RE.sub(lambda m: '<@{}>'.format(m.group(1)), sides[1])
    score_m = re.search(r'\d+\s*-\s*\d', right)
    if score_m:
        right = right[:score_m.start()]
    winners, losers = side_ids(sides[0], sender), side_ids(right, sender)
    if not winners or not losers:
        return None
    return winners, losers


def handles_message(lctx, command_object):
    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    if not is_admin and command_object.channel != lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]:
        return False
    text = command_object.text
    if not (re.match(r'(?i)me\b', text) or text.startswith('<@')):
        return False
    sides = split_sides(text)
    if sides is None or parse_sides(text, command_object.user) is None:
        return False
    left_me, right_me = mentions_me(sides[0]), mentions_me(sides[1])
    if is_admin:
        return not left_me and not right_me
    return left_me != right_me


def get_format_message(lctx):
    example_score = lctx.configs[configs.SCORE_EXAMPLE]
    bot_name = lctx.configs[configs.BOT_NAME]
    message = "Didn't catch that. The format is `{} me over @them {}` or `{} @them over me {}`".format(bot_name, example_score, bot_name, example_score)
    if participants.is_doubles(lctx):
        message += " (tag either opponent; either partner can report)"
    return message


def scores_for_match(match, text):
    # Strip tags before parsing score so labeled mentions with '-' don't confuse parse_score
    clean_text = TAG_RE.sub(' ', text)
    if match.play_all_sets:
        winner_score, loser_score, tie_score = parse_score(clean_text)
        if winner_score + loser_score + tie_score != match.sets_needed:
            raise Exception("Incorrect points")
        return winner_score, loser_score, tie_score
    if match.sets_needed > 1:
        winner_score, loser_score, tie_score = parse_score(clean_text)
        if tie_score > 0:
            raise Exception("Incorrect points")
        if winner_score != match.sets_needed and loser_score != match.sets_needed:
            raise Exception("Incorrect points")
        if winner_score + loser_score < match.sets_needed or winner_score + loser_score >= match.sets_needed * 2:
            raise Exception("Incorrect points")
        return winner_score, loser_score, tie_score
    return 1, 0, 0


def resolve_doubles_sides(resolver, season, sender, winners, losers):
    # Every tagged user must be on a team before any side or partner checks run.
    for user in winners + losers:
        if resolver.participant_for_user(user, season) is None:
            return NOT_ON_TEAM_MSG.format(user)
    # A user on both sides means they played themselves.
    winner_set = set(winners)
    loser_set = set(losers)
    if winner_set & loser_set:
        return PLAYED_YOURSELF_MSG
    side_teams = []
    for side in (winners, losers):
        teams = [(user, resolver.participant_for_user(user, season)) for user in side]
        for user, team_id in teams[1:]:
            if team_id != teams[0][1]:
                return SPLIT_SIDE_MSG.format(teams[0][0], user)
        side_teams.append(teams)
    if side_teams[0][0][1] == side_teams[1][0][1]:
        sender_side = 0 if sender in winners else 1 if sender in losers else None
        if sender_side is not None:
            return YOUR_PARTNER_MSG.format(side_teams[1 - sender_side][0][0])
        return SAME_TEAM_MSG.format(side_teams[0][0][0], side_teams[1][0][0])
    return side_teams[0][0][1], side_teams[1][0][1]


def _record_result(lctx, command_object, winner_id, write, grouping=None):
    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    try:
        if write() is False:
            raise Exception('Match update rejected')
        slack_util.add_reaction(lctx, command_object.channel, command_object.timestamp, WORKED_REACTION)
    except Exception as e:
        slack_util.post_message(lctx, 'Failed to enter into db', lctx.configs[configs.COMMISSIONER_SLACK_ID])
        slack_util.add_reaction(lctx, command_object.channel, command_object.timestamp, NOT_WORKED_REACTION)
        print(e)
        return

    if not is_admin:
        if lctx.configs[configs.MESSAGE_COMMISSIONER_ON_SUCCESS] == 'TRUE':
            slack_util.post_message(lctx, 'Entered into db', lctx.configs[configs.COMMISSIONER_SLACK_ID])
        if grouping is None:
            grouping = participants.resolver(lctx.league_name).grouping_of(winner_id)
        group_msg = group.build_message_for_group(lctx, grouping)
        slack_util.post_message(lctx, group_msg, command_object.channel)


def handle_message(lctx, command_object):
    if lctx.configs[configs.BLOCK_NEW_SCORES] == 'TRUE':
        slack_util.post_message(lctx, BLOCK_NEW_SCORES_MSG, command_object.channel)
        return

    sides = parse_sides(command_object.text, command_object.user)
    if sides is None:
        slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
        return
    if participants.is_doubles(lctx):
        _handle_doubles(lctx, command_object, sides[0], sides[1])
        return
    if len(sides[0]) != 1 or len(sides[1]) != 1:
        slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
        return
    winner_id, loser_id = sides[0][0], sides[1][0]
    if winner_id == loser_id:
        slack_util.post_message(lctx, PLAYED_YOURSELF_MSG, command_object.channel)
        return

    matches = db.get_matches_for_season(lctx.league_name, db.get_current_season(lctx.league_name))
    tmp = [x for x in matches if x.player_1_id == winner_id and x.player_2_id == loser_id or
           x.player_2_id == winner_id and x.player_1_id == loser_id]
    if len(tmp) == 0:
        slack_util.post_message(lctx, NO_MATCH_MSG, command_object.channel)
        return
    try:
        scores = scores_for_match(tmp[0], command_object.text)
    except Exception:
        slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
        return
    _record_result(lctx, command_object, winner_id,
                   lambda: db.update_match_by_id(lctx.league_name, winner_id, loser_id, *scores),
                   grouping=tmp[0].grouping)


def _handle_doubles(lctx, command_object, winners, losers):
    season = db.get_current_season(lctx.league_name)
    resolved = resolve_doubles_sides(participants.resolver(lctx.league_name), season, command_object.user, winners, losers)
    if isinstance(resolved, str):
        slack_util.post_message(lctx, resolved, command_object.channel)
        return
    winner_team, loser_team = resolved
    match = db.get_match_by_participants(lctx.league_name, winner_team, loser_team)
    if match is None:
        slack_util.post_message(lctx, NO_MATCH_MSG, command_object.channel)
        return
    try:
        scores = scores_for_match(match, command_object.text)
    except Exception:
        slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
        return
    _record_result(lctx, command_object, winner_team,
                   lambda: db.update_match_by_participants(lctx.league_name, winner_team, loser_team, *scores),
                   grouping=match.grouping)


def parse_score(message):
    dash_index = message.index('-')
    score_substring = message[dash_index - 1: dash_index + 2]

    winner_score = int(score_substring[0])
    loser_score = int(score_substring[2])
    tie_score = 0

    after_dash = message[dash_index+1:]
    if '-' in after_dash:
        tie_score = int(after_dash[after_dash.index('-')+1:after_dash.index('-')+2])

    return winner_score, loser_score, tie_score
