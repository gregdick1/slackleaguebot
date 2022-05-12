from flask import Blueprint, request, jsonify

from backend import db
from backend.league_context import LeagueContext

league_config_api = Blueprint('league_config_api', __name__)


@league_config_api.route('/get-league-configs', methods=['GET'])
def get_league_configs():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify({})

    # TODO return subset of configs?
    return jsonify(LeagueContext.load_from_db(league_name).configs)


@league_config_api.route('/set-league-config', methods=['POST'])
def set_league_config():
    data = request.get_json()
    league_name = data.get('selectedLeague')
    if not league_name:
        return "no-op"
    config_key = data.get('configKey')
    config_value = data.get('configValue')
    db.set_config(league_name, config_key, config_value)
    return "Success"
