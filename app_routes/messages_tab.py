from flask import Blueprint, request

from admin import admin_config
from backend import slack_util
from backend.league_context import LeagueContext

messages_api = Blueprint('messages_api', __name__)


# TODO download the db before sending messages
@messages_api.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    league_name = admin_config.get_current_league()
    lctx = LeagueContext.load_from_db(league_name)
    if "@against_user" in message:
        response = slack_util.send_match_messages(lctx, message, debug=True)
    else:
        response = slack_util.send_custom_messages(lctx, message, debug=True)

    if response is None or response == "":
        response = "No messages sent."

    return response


@messages_api.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    league_name = admin_config.get_current_league()
    lctx = LeagueContext.load_from_db(league_name)
    if "@against_user" in message:
        response = slack_util.send_match_messages(lctx, message, debug=False)
    else:
        response = slack_util.send_custom_messages(lctx, message, debug=False)

    if response is None or response == "":
        response = "No messages sent."

    return response
