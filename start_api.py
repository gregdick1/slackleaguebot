import json

from flask import Flask, render_template, request, jsonify
from backend import db, match_making, slack
import datetime

from backend.config_db import set_config

app = Flask(__name__, template_folder="./build", static_folder="./build/static")


@app.route('/')
def serve_fronted():
    return render_template("index.html")


@app.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    response = ""
    if "@against_user" in message:
        response = slack.send_match_messages(message, debug=True)
    else:
        response = slack.send_custom_messages(message, debug=True)

    if response is None or response == "":
        response = "No messages sent."

    return response


@app.route('/set-config-value', methods=['POST'])
def set_config_value():
    config = request.get_json()
    print(config)

    for key, value in config.items():
        set_config(key, value)

    return "Nicely done. You configured the heck out of the configuration!"


@app.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    response = ""
    if "@against_user" in message:
        response = slack.send_match_messages(message, debug=False)
    else:
        response = slack.send_custom_messages(message, debug=False)

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

    match_making.create_matches_for_season(next_monday, skip_weeks=[], include_byes=False)

    return "We did it boys"


@app.route('/update-match-info', methods=['POST'])
def update_match_info():
    updated_match_info = request.get_json();
    print(updated_match_info);

    db.admin_update_match(updated_match_info);

    return "The commissioner has spoken. The match has been updated."



def ensure_players_in_db(players):
    existing_players_dict = dict()
    existing_players = db.get_players()

    for existing_player in existing_players:
        existing_players_dict[existing_player.name] = existing_player

    players_to_add = []
    for player in players:
        if player['name'] not in existing_players_dict:
            print("FOUND ONE", player['name'])
            players_to_add.append(player)

    if len(players_to_add) == 0:
        return

    # Get users list
    response = slack.slack_client.users.list()
    users = response.body['members']
    user_map = {}
    for user in users:
        for player in players_to_add:
            if user['profile']['real_name'].startswith(player['name']) and not user['deleted']:
                user_map[player['name']] = user['id']
                db.add_player(user['id'], player['name'], player['group'])


def update_groupings(group, players):
    existing = db.get_players()

    for player in players:
        for e in existing:
            if e.name == player['name']:
                if group == 'Trash':
                    db.update_grouping(e.slack_id, "")
                    db.set_active(e.slack_id, False)
                else:
                    db.update_grouping(e.slack_id, group)
                    db.set_active(e.slack_id, True)


@app.route('/get-active-players', methods=['GET'])
def get_active_players():
    players = get_ranked_players()

    return jsonify(players)


@app.route('/get-current-matches', methods=['GET'])
def get_current_matches():
    season = db.get_current_season()
    current_season_matches = db.get_matches_for_season(season)
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
    season = db.get_current_season()
    all_matches = db.get_matches_for_season(season)
    all_players = db.get_players()

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


if __name__ == '__main__':
    app.run()
