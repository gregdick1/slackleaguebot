from backend import configs
from backend.commands import enter_score, help, group, leaderboard, week_matches, user_stats, group_analysis, matchup_history
from backend.commands.command_message import CommandMessage


def trusted_reporter_ids(lctx):
    raw = lctx.configs.get(configs.TRUSTED_REPORTER_IDS) or ''
    return {i.strip() for i in raw.split(',') if i.strip()}


def is_trusted_reporter(lctx, message_object):
    """A bot (never a human, never this bot) whose bot_id or user id is in TRUSTED_REPORTER_IDS."""
    if not message_object.get('bot_id'):
        return False
    sender_ids = {message_object['bot_id'], message_object.get('user')} - {None}
    if lctx.configs.get(configs.BOT_SLACK_USER_ID) in sender_ids:
        return False
    return bool(sender_ids & trusted_reporter_ids(lctx))


def validate_and_clean_message(lctx, message_object):
    if message_object is None:
        return None

    is_trusted = False
    if 'bot_id' in message_object:
        if not is_trusted_reporter(lctx, message_object):
            return None
        is_trusted = True
        # Legacy bot_message events carry no user
        message_object.setdefault('user', message_object['bot_id'])

    if 'text' not in message_object or 'channel' not in message_object or 'user' not in message_object or 'ts' not in message_object:
        return None

    bot_id = lctx.configs[configs.BOT_SLACK_USER_ID]
    channel_id = lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]
    message_text = message_object['text']
    if is_trusted:
        # A trusted bot only reports in the competition channel, never in a DM
        if message_object['channel'] != channel_id or not message_text.startswith('<@' + bot_id + '>'):
            return None
        message_object['text'] = message_text[message_text.index(">") + 1:].strip()
        message_object['trusted_reporter'] = True
        return message_object

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
    return CommandMessage(text, channel, user_id, timestamp, message_object.get('trusted_reporter', False))


def determine_command(lctx, message_object):
    command_message = get_command_object(message_object)
    if command_message.is_trusted_reporter:
        # A trusted bot only reports scores
        return enter_score if enter_score.handles_message(lctx, command_message) else None

    # The order of these commands is important. It will try them one at a time to see who should handle the command
    commands = [
        help,
        group,
        enter_score,
        leaderboard,
        week_matches,
        user_stats,
        group_analysis,
        matchup_history
    ]

    for command in commands:
        if command.handles_message(lctx, command_message):
            return command
    return None
