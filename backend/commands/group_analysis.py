from backend import slack_util
from backend.scenario_analysis import scenario_predictor

MISFORMAT_MSG = 'Not a group. Format is simply `Analyze Group A`'
NOT_A_GROUP_MSG = 'Not a group (or I messed up).'


def handles_message(lctx, command_object):
    if command_object.text.upper().startswith('ANALYZE GROUP '):
        return True
    return False


def handle_message(lctx, command_object):
    text = command_object.text[6:]
    if len(text) != 1:
        slack_util.post_message(lctx, MISFORMAT_MSG, command_object.channel)
        return

    group = text[0].upper()
    message = scenario_predictor.analyze_group_possibilities(lctx.league_name, group)
    if message is None:
        slack_util.post_message(lctx, NOT_A_GROUP_MSG, command_object.channel)
    else:
        slack_util.post_message(lctx, message, command_object.channel)
