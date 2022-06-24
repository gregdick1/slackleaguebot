from flask import Blueprint, request, jsonify

from admin import admin_context, db_management
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


@messages_api.route('/trigger-reminders', methods=['POST'])
def manual_trigger_reminders():
    league_name = request.get_json().get("leagueName")
    try:
        context = admin_context.Context.load_from_db(league_name)
        db_management.download_db(context)
        reminders.run_reminders(league_name, debug=False, force=True)
        # print('Ran reminders')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@messages_api.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")
    league_name = request.get_json().get("leagueName")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    lctx = LeagueContext.load_from_db(league_name)
    response = slack_util.send_custom_messages(lctx, message, debug=True)

    if response is None or response == "":
        response = "No messages sent."

    return response


@messages_api.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")
    league_name = request.get_json().get("leagueName")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    lctx = LeagueContext.load_from_db(league_name)
    response = slack_util.send_custom_messages(lctx, message, debug=False)

    if response is None or response == "":
        response = "No messages sent."

    return response
