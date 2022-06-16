from flask import Blueprint, request, jsonify

from admin import admin_config
from backend import slack_util, db, reminders
from backend.league_context import LeagueContext

messages_api = Blueprint('messages_api', __name__)


@messages_api.route('/get-reminder-days', methods=['GET'])
def get_reminder_days():
    league_name = request.args.get("leagueName", default="", type=str)
    season = request.args.get("season", default="", type=int)
    reminder_days = db.get_reminder_days_for_season(league_name, season)
    return jsonify(reminder_days)


@messages_api.route('/update-reminder-days', methods=['POST'])
def update_reminder_days():
    data = request.get_json()
    league_name = data.get("leagueName")
    season = data.get("season")
    dates = data.get("dates")
    reminders.update_reminders_days(league_name, season, dates)
    return "Success"


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
