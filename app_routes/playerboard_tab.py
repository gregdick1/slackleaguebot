import datetime

from flask import Blueprint, request, jsonify

from admin import admin_config
from backend import db, league_context, slack, match_making, utility

playerboard_api = Blueprint('playerboard_api', __name__)


def _get_league_context():
    lctx = league_context.LeagueContext(admin_config.get_current_league())
    return lctx


def _get_slack_client():
    slack_client = slack.LeagueSlackClient(admin_config.get_current_league())
    return slack_client


@playerboard_api.route('/submit-players', methods=['POST'])
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
    # TODO use the config for sets needed
    match_making.create_matches_for_season(lctx, next_monday, 3, skip_weeks=[], include_byes=False)

    return "We did it boys"

@playerboard_api.route('/get-active-players', methods=['GET'])
def get_active_players():
    players = get_ranked_players()
    return jsonify(players)


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


def get_ranked_players():
    lctx = _get_league_context()
    season = db.get_current_season(lctx)
    all_matches = db.get_matches_for_season(lctx, season)
    all_players = db.get_players(lctx)

    groups = sorted(list(set([m.grouping for m in all_matches])))
    return_players = []

    for group in groups:
        group_matches = [m for m in all_matches if m.grouping == group]

        players = utility.gather_scores(group_matches)

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