import json

from flask import Flask, render_template, request, jsonify
from backend import db, match_making, slack, league_context, bot_config
from admin import admin_config
import datetime


app = Flask(__name__, template_folder="./build", static_folder="./build/static")


def _get_league_context():
    lctx = league_context.LeagueContext(get_current_league())
    return lctx


def _get_slack_client():
    slack_client = slack.LeagueSlackClient(get_current_league())
    return slack_client


@app.route('/')
def serve_fronted():
    return render_template("index.html")


@app.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    slack_client = _get_slack_client()
    response = ""
    if "@against_user" in message:
        response = slack_client.send_match_messages(message, debug=True)
    else:
        response = slack_client.send_custom_messages(message, debug=True)

    if response is None or response == "":
        response = "No messages sent."

    return response


@app.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    slack_client = _get_slack_client()
    response = ""
    if "@against_user" in message:
        response = slack_client.send_match_messages(message, debug=False)
    else:
        response = slack_client.send_custom_messages(message, debug=False)

    if response is None or response == "":
        response = "No messages sent."

    return response


@app.route('/submit-players', methods=['POST'])
def submit_players():
    players_and_groups = request.get_json().get("players")

    for group, players in players_and_groups.items():
        print(group, players)

        ensure_players_in_db(players)
        update_groupings(group, players)

    today = datetime.datetime.today()
    last_monday = today - datetime.timedelta(days=today.weekday())
    next_monday = (last_monday + datetime.timedelta(days=7)).date()

    lctx = _get_league_context()
    match_making.create_matches_for_season(lctx, next_monday, skip_weeks=[], include_byes=False)

    return "We did it boys"


@app.route('/update-match-info', methods=['POST'])
def update_match_info():
    updated_match_info = request.get_json()
    print(updated_match_info)

    lctx = _get_league_context()
    db.admin_update_match(lctx, updated_match_info)

    return "The commissioner has spoken. The match has been updated."


def ensure_players_in_db(players):
    lctx = _get_league_context()
    existing_players_dict = dict()
    existing_players = db.get_players(lctx)

    for existing_player in existing_players:
        existing_players_dict[existing_player.name] = existing_player

    players_to_add = []
    for player in players:
        if player['name'] not in existing_players_dict:
            print("FOUND ONE", player['name'])
            players_to_add.append(player)

    if len(players_to_add) == 0:
        return

    response = _get_slack_client().slack_client.api_call('users.list')
    users = response['members']
    user_map = {}
    for user in users:
        for player in players_to_add:
            if user['profile']['real_name'].startswith(player['name']) and not user['deleted']:
                user_map[player['name']] = user['id']
                db.add_player(lctx, user['id'], player['name'], player['group'])


def update_groupings(group, players):
    lctx = _get_league_context()
    existing = db.get_players(lctx)

    for player in players:
        for e in existing:
            if e.name == player['name']:
                if group == 'Trash':
                    db.update_grouping(lctx, e.slack_id, "")
                    db.set_active(lctx, e.slack_id, False)
                else:
                    db.update_grouping(lctx, e.slack_id, group)
                    db.set_active(lctx, e.slack_id, True)


@app.route('/get-active-players', methods=['GET'])
def get_active_players():
    players = get_ranked_players()

    return jsonify(players)


@app.route('/get-current-matches', methods=['GET'])
def get_current_matches():
    lctx = _get_league_context()
    season = db.get_current_season(lctx, )
    current_season_matches = db.get_matches_for_season(lctx, season)
    return json.dumps(current_season_matches, default=default)


@app.route('/get-current-config', methods=['GET'])
def get_current_config():
    config = get_current_config()
    return jsonify(config)


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o.__dict__


def get_ranked_players():
    lctx = _get_league_context()
    season = db.get_current_season(lctx)
    all_matches = db.get_matches_for_season(lctx, season)
    all_players = db.get_players(lctx)

    groups = sorted(list(set([m.grouping for m in all_matches])))
    return_players = []

    for group in groups:
        group_matches = [m for m in all_matches if m.grouping == group]

        players = match_making.gather_scores(group_matches)

        for player in players:
            name = [p.name for p in all_players if p.slack_id == player['player_id']][0]
            return_players.append(
                {
                    'name': name,
                    'slack_id': player['player_id'],
                    'sets_won': player['s_w'],
                    'sets_lost': player['s_l'],
                    'games_won': player['m_w'],
                    'games_lost': player['m_l'],
                    'group': group
                }
            )

    return return_players


@app.route('/get-leagues-to-admin', methods=['GET'])
def get_leagues_to_admin():
    leagues = admin_config.get_leagues()
    return jsonify(leagues)


@app.route('/get-current-league', methods=['GET'])
def get_current_league():
    return jsonify(admin_config.get_current_league())


@app.route('/set-current-league', methods=['POST'])
def set_current_league():
    league_name = request.get_json().get("selectedLeague")
    admin_config.set_current_league(league_name)
    return "Success"


@app.route('/get-league-admin-configs', methods=['GET'])
def get_league_admin_configs():
    league_name = request.args.get("leagueName", default="", type=str)
    configs = admin_config.get_league_configs(league_name)
    return jsonify(configs)


@app.route('/set-league-admin-config', methods=['POST'])
def set_league_admin_config():
    data = request.get_json()
    league_name = data.get('selectedLeague')
    config_key = data.get('configKey')
    config_value = data.get('configValue')
    admin_config.set_config(league_name, config_key, config_value)
    return "Success"


@app.route('/add-league', methods=['POST'])
def add_league():
    data = request.get_json()
    league_name = data.get('newLeagueName')
    server_options = data.get('leagueAdminConfigs')
    admin_config.add_league(league_name, server_options)
    return "Success"


@app.route('/get-league-configs', methods=['GET'])
def get_league_configs():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify({})
    configs = bot_config.BotConfig(league_name).get_all_configs()
    return jsonify(configs)


@app.route('/set-league-config', methods=['POST'])
def set_league_config():
    data = request.get_json()
    league_name = data.get('selectedLeague')
    config_key = data.get('configKey')
    config_value = data.get('configValue')
    db.set_config(league_context.LeagueContext(league_name), config_key, config_value)
    return "Success"


if __name__ == '__main__':
    app.run()
