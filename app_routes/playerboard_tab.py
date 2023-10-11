import datetime, json

from flask import Blueprint, request, jsonify

from admin import admin_config
from backend import db, match_making, utility, slack_util
from backend.league_context import LeagueContext

playerboard_api = Blueprint('playerboard_api', __name__)


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

    league_name = admin_config.get_current_league()
    lctx = LeagueContext.load_from_db(league_name)
    # TODO use the config for sets needed
    match_making.create_matches_for_season(lctx, next_monday, 3, skip_weeks=[], include_byes=False)

    return "We did it boys"


@playerboard_api.route('/get-active-players', methods=['GET'])
def get_active_players():
    players = get_ranked_players()
    return jsonify(players)


@playerboard_api.route('/get-players-from-season', methods=['GET'])
def get_players_from_season():
    league_name = request.args.get("leagueName", default="", type=str)
    season = request.args.get("season", default=0, type=int)
    players = get_ranked_players(league_name, season)
    return jsonify(players)


@playerboard_api.route('/get-all-seasons', methods=['GET'])
def get_all_seasons():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify([])
    all_seasons = db.get_all_seasons(league_name)
    return jsonify(all_seasons)


@playerboard_api.route('/inactivate-player', methods=['POST'])
def inactivate_player():
    league_name = request.get_json().get("leagueName")
    player_id = request.get_json().get("playerId")

    db.update_grouping(league_name, player_id, '')
    db.set_active(league_name, player_id, False)
    return "success"


@playerboard_api.route('/update-player-grouping-and-orders', methods=['POST'])
def update_player_grouping():
    data = request.get_json()
    league_name = data.get("leagueName")
    grouping = data.get("grouping")
    players = data.get("players")

    db.updating_grouping_and_orders(league_name, players, grouping)
    return "success"


@playerboard_api.route('/add-player', methods=['POST'])
def add_player():
    data = request.get_json()
    league_name = data.get("leagueName")
    player_name = data.get("playerName")
    grouping = data.get("grouping")
    lctx = LeagueContext.load_from_db(league_name)
    slack_id = slack_util.get_slack_id(lctx, player_name)
    if slack_id is None:
        return jsonify({'success': False, 'message': 'Could not find slack id for {}'.format(player_name)})
    try:
        db.add_player(league_name, slack_id, player_name, grouping)
        p = db.get_player_by_id(league_name, slack_id)
        return jsonify({'success': True, 'player': json.dumps(p, default=match_player_serializer)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@playerboard_api.route('/refresh-users', methods=['POST'])
def refresh_users():
    data = request.get_json()
    league_name = data.get("leagueName")
    lctx = LeagueContext.load_from_db(league_name)
    try:
        users_list = slack_util._get_users_list(lctx, True)
        return jsonify({'success': True, 'totalUsers': len(users_list), 'lastRan': slack_util.last_get_users_date})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@playerboard_api.route('/slack-users-count', methods=['GET'])
def refresh_users_info():
    return jsonify({'success': True, 'totalUsers': len(slack_util.users_list), 'lastRan': slack_util.last_get_users_date})


@playerboard_api.route('/get-deactivated-players', methods=['GET'])
def get_deactivated_players():
    league_name = request.args.get("leagueName", default="", type=str)
    lctx = LeagueContext.load_from_db(league_name)
    return jsonify(slack_util.get_deactivated_slack_ids(lctx))


def ensure_players_in_db(players):
    league_name = admin_config.get_current_league()  # TODO pass league name in
    existing_players_dict = dict()
    existing_players = db.get_players(league_name)

    for existing_player in existing_players:
        existing_players_dict[existing_player.name] = existing_player

    players_to_add = []
    for player in players:
        if player['name'] not in existing_players_dict:
            print("FOUND ONE", player['name'])
            players_to_add.append(player)

    if len(players_to_add) == 0:
        return

    # TODO move this to slack util if we're gonna keep it
    lctx = LeagueContext.load_from_db(league_name)
    users = slack_util._get_users_list(lctx)
    user_map = {}
    for user in users:
        for player in players_to_add:
            if user['profile']['real_name'].startswith(player['name']) and not user['deleted']:
                user_map[player['name']] = user['id']
                db.add_player(league_name, user['id'], player['name'], player['group'])


def update_groupings(group, players):
    league_name = admin_config.get_current_league()
    existing = db.get_players(league_name)

    for player in players:
        for e in existing:
            if e.name == player['name']:
                if group == 'Trash':
                    db.update_grouping(league_name, e.slack_id, "")
                    db.set_active(league_name, e.slack_id, False)
                else:
                    db.update_grouping(league_name, e.slack_id, group)
                    db.set_active(league_name, e.slack_id, True)


def get_ranked_players(league_name=None, season=None):
    league_name = league_name or admin_config.get_current_league()
    if season is None:
        season = db.get_current_season(league_name)
    all_matches = db.get_matches_for_season(league_name, season)
    all_players = db.get_players(league_name)

    groups = sorted(list(set([m.grouping for m in all_matches])))
    return_players = []

    for group in groups:
        group_matches = [m for m in all_matches if m.grouping == group]

        players = utility.gather_scores(group_matches)

        for player in players:
            if player['player_id'] is None:
                continue

            name = [p.name for p in all_players if p.slack_id is not None and p.slack_id == player['player_id']][0]
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


def match_player_serializer(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o.__dict__
