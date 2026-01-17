from backend import configs
from backend.commands import enter_score, help, group, leaderboard, week_matches, user_stats, group_analysis, matchup_history, record
from backend.commands.command_message import CommandMessage


def validate_and_clean_message(lctx, message_object):
    if message_object is None:
        return None

    if 'text' not in message_object or 'channel' not in message_object or 'user' not in message_object or 'ts' not in message_object:
        return None

    if 'bot_id' in message_object:
        return None

    bot_id = lctx.configs[configs.BOT_SLACK_USER_ID]
    channel_id = lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]
    message_text = message_object['text']
    if message_object['channel'][:1] == 'D':
        if message_text.startswith('<@' + bot_id + '>'):
            message_text = message_text[message_text.index(">") + 1:].strip()

        message_object['text'] = message_text
        return message_object

    if message_object['channel'] == channel_id and message_text.startswith('<@' + bot_id + '>'):
        message_text = message_text[message_text.index(">") + 1:].strip()

        message_object['text'] = message_text
        return message_object


def get_command_object(message_object):
    text = message_object["text"]
    channel = message_object["channel"]
    user_id = message_object["user"]
    timestamp = message_object["ts"]
    return CommandMessage(text, channel, user_id, timestamp)


def determine_command(lctx, message_object):
    command_message = get_command_object(message_object)

    # The order of these commands is important. It will try them one at a time to see who should handle the command
    commands = [
        help,
        group,
        enter_score,
        leaderboard,
        week_matches,
        record,
        user_stats,
        group_analysis,
        matchup_history
    ]

    for command in commands:
        if command.handles_message(lctx, command_message):
            return command
    return None
