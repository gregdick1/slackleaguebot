from flask import Blueprint, request

from admin import admin_config
from backend import league_context, slack

messages_api = Blueprint('messages_api', __name__)


def _get_league_context():
    lctx = league_context.LeagueContext(admin_config.get_current_league())
    return lctx


def _get_slack_client():
    slack_client = slack.LeagueSlackClient(admin_config.get_current_league())
    return slack_client


@messages_api.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    slack_client = _get_slack_client()
    if "@against_user" in message:
        response = slack_client.send_match_messages(message, debug=True)
    else:
        response = slack_client.send_custom_messages(message, debug=True)

    if response is None or response == "":
        response = "No messages sent."

    return response


@messages_api.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    slack_client = _get_slack_client()
    if "@against_user" in message:
        response = slack_client.send_match_messages(message, debug=False)
    else:
        response = slack_client.send_custom_messages(message, debug=False)

    if response is None or response == "":
        response = "No messages sent."

    return response
