from flask import Blueprint, request, jsonify

from backend import db, bot_config, league_context

league_config_api = Blueprint('league_config_api', __name__)


@league_config_api.route('/get-league-configs', methods=['GET'])
def get_league_configs():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify({})
    configs = bot_config.BotConfig(league_name).get_all_configs()
    return jsonify(configs)


@league_config_api.route('/set-league-config', methods=['POST'])
def set_league_config():
    data = request.get_json()
    league_name = data.get('selectedLeague')
    config_key = data.get('configKey')
    config_value = data.get('configValue')
    db.set_config(league_context.LeagueContext(league_name), config_key, config_value)
    return "Success"
