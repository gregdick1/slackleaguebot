from backend import slack_util, configs, db, utility
NO_MATCH_MSG = "I couldn't find a match between you two."

def handles_message(lctx, command_object):
    is_admin = command_object.user == lctx.configs[configs.COMMISSIONER_SLACK_ID] and command_object.is_dm()
    if not is_admin and command_object.channel != lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]:
        return False
    if command_object.text.upper().startswith('RECORD') and not is_admin:
        return True
    return False


def get_format_message(lctx):
    return 'aaaaaaaa'


def handle_message(lctx, command_object):
    players = parse_users(command_object)
    if players:
        if players['first_id'] == players['second_id']:
            slack_util.post_message(lctx, 'You are attempting to get the match record between yourself and yourself :bigbrain:', command_object.channel)
            return
        record = utility.get_players_record(lctx, players['first_id'], players['second_id'])
        p1 = db.get_player_by_id(lctx.league_name, players['first_id'])
        p2 = db.get_player_by_id(lctx.league_name, players['second_id'])

        if record['p1_wins'] + record['p2_wins'] == 0:
            slack_util.post_message(lctx, '{} and {} never played a match together.'.format(p1.name, p2.name), command_object.channel)
            return

        if record['p1_wins'] != record['p2_wins']:
            better_player = [p1, record['p1_wins']] if record['p1_wins'] > record['p2_wins'] else [p2, record['p2_wins']]
            worse_player = [p1, record['p1_wins']] if record['p1_wins'] < record['p2_wins'] else [p2, record['p2_wins']]
            slack_util.post_message(lctx, '{} is {}-{} against {}.'.format(better_player[0].name, better_player[1],
                                                                               worse_player[1], worse_player[0].name), command_object.channel)
        else:
            slack_util.post_message(lctx, '{} and {} are tied at {} win(s) each.'.format(p1.name, p2.name, record['p1_wins']), command_object.channel)




def parse_first_slack_id(message):
    return message[message.index('<@') + 2: message.index('>')]


def parse_second_slack_id(message):
    message = message[message.index('>') + 1:]
    return parse_first_slack_id(message)


def parse_users(command_object):
    command = command_object.text
    try:
        player1 = parse_first_slack_id(command)
        player2 = parse_second_slack_id(command)
        return {
            'first_id': player1,
            'second_id': player2
        }
    except:
        return
