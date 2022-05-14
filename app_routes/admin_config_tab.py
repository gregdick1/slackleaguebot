from flask import Blueprint, request, jsonify

from admin import admin_config, admin_context, sftp, deploy

admin_api = Blueprint('admin_api', __name__)


@admin_api.route('/get-league-admin-configs', methods=['GET'])
def get_league_admin_configs():
    league_name = request.args.get("leagueName", default="", type=str)
    configs = admin_config.get_league_configs(league_name)
    return jsonify(configs)


@admin_api.route('/set-league-admin-config', methods=['POST'])
def set_league_admin_config():
    data = request.get_json()
    league_name = data.get('selectedLeague')
    config_key = data.get('configKey')
    config_value = data.get('configValue')
    admin_config.set_config(league_name, config_key, config_value)
    admin_config.set_config(league_name, admin_config.HAS_CONNECTED, str(False))
    return "Success"


@admin_api.route('/add-league', methods=['POST'])
def add_league():
    data = request.get_json()
    league_name = data.get('newLeagueName')
    server_options = data.get('leagueAdminConfigs')
    admin_config.add_league(league_name, server_options)
    return "Success"


@admin_api.route('/check-server-connection', methods=['POST'])
def check_server_connection():
    league_name = request.get_json().get('leagueName')
    try:
        sftp.try_connect_to_server(admin_context.Context.load_from_db(league_name))
        admin_config.set_config(league_name, admin_config.HAS_CONNECTED, str(True))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@admin_api.route('/deploy-to-server', methods=['POST'])
def deploy_to_server():
    league_name = request.get_json().get('leagueName')
    try:
        message = deploy.deploy_league(league_name)
        admin_config.set_config(league_name, admin_config.HAS_DEPLOYED, str(True))
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
