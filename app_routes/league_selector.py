from flask import Blueprint, request, jsonify

from admin import admin_config, db_management, admin_context
from backend import db, league_context

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


@league_selector_api.route('/get-last-db-refresh', methods=['GET'])
def get_last_db_refresh():
    league_name = request.args.get("leagueName", default="", type=str)
    time_str = admin_config.get_config(league_name, admin_config.LAST_DOWNLOADED)
    return jsonify(time_str)


@league_selector_api.route('/refresh-db', methods=['POST'])
def refresh_db():
    league_name = request.get_json().get("leagueName")
    try:
        context = admin_context.Context.load_from_db(league_name)
        db_management.download_db(context)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@league_selector_api.route('/get-commands-to-run', methods=['GET'])
def get_commands_to_run():
    league_name = request.args.get("leagueName", default="", type=str)
    ctr = db.get_commands_to_run(league_context.LeagueContext(league_name))
    return jsonify(len(ctr))


@league_selector_api.route('/push-updates-to-server', methods=['POST'])
def push_updates_to_server():
    league_name = request.get_json().get("leagueName")
    try:
        context = admin_context.Context.load_from_db(league_name)
        message = db_management.commit_commands(context)
        if message:
            return jsonify({'success': False, 'message': message})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
