from flask import Blueprint, request, jsonify

from admin import admin_config

league_selector_api = Blueprint('league_selector_api', __name__)


@league_selector_api.route('/get-leagues-to-admin', methods=['GET'])
def get_leagues_to_admin():
    leagues = admin_config.get_leagues()
    return jsonify(leagues)


@league_selector_api.route('/get-current-league', methods=['GET'])
def get_current_league():
    return jsonify(admin_config.get_current_league())


@league_selector_api.route('/set-current-league', methods=['POST'])
def set_current_league():
    league_name = request.get_json().get("selectedLeague")
    admin_config.set_current_league(league_name)
    return "Success"
