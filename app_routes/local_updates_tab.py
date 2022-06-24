from flask import Blueprint, request, jsonify

from backend import db

local_updates_api = Blueprint('local_updates_api', __name__)


@local_updates_api.route('/get-local-updates', methods=['GET'])
def get_reminder_days():
    league_name = request.args.get("leagueName", default="", type=str)
    updates = db.get_commands_to_run(league_name)
    return jsonify(updates)