from backend import slack_util, configs, db, utility
from backend.commands import group

BLOCK_NEW_SCORES_MSG = "Sorry, not accepting any scores at this time."
PLAYED_YOURSELF_MSG = "You can't play against yourself."
NO_MATCH_MSG = "I couldn't find a match between you two."
WORKED_REACTION = "white_check_mark"
NOT_WORKED_REACTION = "x"


def handles_message(lctx, command_object):
    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    if not is_admin and command_object.channel != lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]:
        return False
    if command_object.text.upper().startswith('ME OVER <@') and not is_admin:
        return True
    if command_object.text.startswith('<@'):
        text = command_object.text[command_object.text.index('>')+1:].upper()
        if text.startswith(' OVER ME') and not is_admin:
            return True
        if text.startswith(' OVER <@') and command_object.is_dm() and command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID]:
            return True
    return False


def get_format_message(lctx):
    example_score = lctx.configs[configs.SCORE_EXAMPLE]
    bot_name = lctx.configs[configs.BOT_NAME]
    return "Didn't catch that. The format is `{} me over @them {}` or `{} @them over me {}`".format(bot_name, example_score, bot_name, example_score)


def handle_message(lctx, command_object):
    if lctx.configs[configs.BLOCK_NEW_SCORES] == 'TRUE':
        slack_util.post_message(lctx, BLOCK_NEW_SCORES_MSG, command_object.channel)
        return

    users = parse_users(lctx, command_object)
    if users is None:
        slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
        return
    if users['winner_id'] == users['loser_id']:
        slack_util.post_message(lctx, PLAYED_YOURSELF_MSG, command_object.channel)
        return

    matches = db.get_matches_for_season(lctx.league_name, db.get_current_season(lctx.league_name))
    tmp = [x for x in matches if x.player_1_id == users['winner_id'] and x.player_2_id == users['loser_id'] or
           x.player_2_id == users['winner_id'] and x.player_1_id == users['loser_id']]
    if len(tmp) == 0:
        slack_util.post_message(lctx, NO_MATCH_MSG, command_object.channel)
        return

    match = tmp[0]
    winner_score = 0
    loser_score = 0
    tie_score = 0
    if match.play_all_sets:  # Total score needs to match the sets_needed value
        try:
            winner_score, loser_score, tie_score = parse_score(command_object.text)
            if winner_score + loser_score + tie_score != match.sets_needed:
                raise Exception("Incorrect points")
        except Exception as e:
            slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
            return
    elif match.sets_needed > 1:
        try:
            winner_score, loser_score, tie_score = parse_score(command_object.text)
            if tie_score > 0:
                raise Exception("Incorrect points")
            if winner_score != match.sets_needed and loser_score != match.sets_needed:
                raise Exception("Incorrect points")
            if winner_score + loser_score < match.sets_needed or winner_score + loser_score >= match.sets_needed*2:
                raise Exception("Incorrect points")
        except Exception as e:
            slack_util.post_message(lctx, get_format_message(lctx), command_object.channel)
            return
    else:
        winner_score = 1

    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    try:
        db.update_match_by_id(lctx.league_name, users['winner_id'], users['loser_id'], winner_score, loser_score, tie_score)
        slack_util.add_reaction(lctx, command_object.channel, command_object.timestamp, WORKED_REACTION)

    except Exception as e:
        slack_util.post_message(lctx, 'Failed to enter into db', lctx.configs[configs.COMMISSIONER_SLACK_ID])
        slack_util.add_reaction(lctx, command_object.channel, command_object.timestamp, NOT_WORKED_REACTION)
        print(e)
        return

    if not is_admin:
        if lctx.configs[configs.MESSAGE_COMMISSIONER_ON_SUCCESS] == 'TRUE':
            slack_util.post_message(lctx, 'Entered into db', lctx.configs[configs.COMMISSIONER_SLACK_ID])
        player = db.get_player_by_id(lctx.league_name, users['winner_id'])
        group_msg = group.build_message_for_group(lctx, player.grouping)
        rivalry_msg = build_message_for_rivalry_record(lctx, users['winner_id'], users['loser_id'])
        slack_util.post_message(lctx, '{}\n{}'.format(rivalry_msg, group_msg), command_object.channel)


def build_message_for_rivalry_record(lctx, p1_id, p2_id):
    record = utility.get_players_record(lctx, p1_id, p2_id)
    p1 = db.get_player_by_id(lctx.league_name, p1_id)
    p2 = db.get_player_by_id(lctx.league_name, p2_id)
    include_oof = True if abs(record['p1_wins'] - record['p2_wins']) > 5 else False
    return '_{} is now {}-{} against {}._{}'.format(
        p1.name, record['p1_wins'], record['p2_wins'], p2.name, ' :oof:' if include_oof else '')


def parse_first_slack_id(message):
    return message[message.index('<@') + 2: message.index('>')]


def parse_second_slack_id(message):
    message = message[message.index('>') + 1:]
    return parse_first_slack_id(message)


def parse_users(lctx, command_object):
    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    command = command_object.text
    if command.upper().startswith('ME OVER '):
        winner = command_object.user
        loser = parse_first_slack_id(command)
    elif is_admin and command.startswith('<@'):
        winner = parse_first_slack_id(command)
        loser = parse_second_slack_id(command)
    elif command.startswith('<@') and command.upper().index('OVER ME') > 0:
        winner = parse_first_slack_id(command)
        loser = command_object.user
    else:
        # self.logger.debug('Bad message format') TODO
        return None

    return {
        'winner_id': winner,
        'loser_id': loser
    }


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
