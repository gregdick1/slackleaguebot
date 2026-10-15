import datetime, json

from flask import Blueprint, request, jsonify

from admin import admin_config
from backend import db, utility, slack_util, participants
from backend.league_context import LeagueContext

playerboard_api = Blueprint('playerboard_api', __name__)


def _team_json(r, team):
    return {'team_id': team.team_id, 'name': team.name, 'member_1': team.member_1, 'member_2': team.member_2,
            'grouping': team.grouping, 'order_idx': team.order_idx, 'display_name': r.display_name(team.team_id)}


def _team_action(work):
    try:
        result = work() or {}
        return jsonify(dict({'success': True}, **result))
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({'success': False, 'message': str(e)})


@playerboard_api.route('/get-draft-teams', methods=['GET'])
def get_draft_teams():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify({'success': False, 'message': 'leagueName is required.'})
    season = db.get_current_season(league_name) + 1
    r = participants.resolver(league_name)
    return jsonify({'success': True, 'season': season, 'teams': [_team_json(r, t) for t in db.get_teams_for_season(league_name, season)]})


@playerboard_api.route('/add-team', methods=['POST'])
def add_team():
    data = request.get_json()
    league_name = data.get('leagueName')
    season = db.get_current_season(league_name) + 1
    return _team_action(lambda: {'teamId': db.add_team(league_name, season, data.get('member1'), data.get('member2'), data.get('grouping'), name=data.get('name'))})


@playerboard_api.route('/update-team', methods=['POST'])
def update_team():
    data = request.get_json()
    kwargs = {'member_1': data.get('member1'), 'member_2': data.get('member2')}
    if 'name' in data:
        kwargs['name'] = data.get('name')
    return _team_action(lambda: db.update_team(data.get('leagueName'), data.get('teamId'), **kwargs))


@playerboard_api.route('/delete-team', methods=['POST'])
def delete_team():
    data = request.get_json()
    return _team_action(lambda: db.delete_team(data.get('leagueName'), data.get('teamId')))


@playerboard_api.route('/update-team-grouping-and-orders', methods=['POST'])
def update_team_grouping_and_orders():
    data = request.get_json()
    return _team_action(lambda: db.update_team_grouping_and_orders(data.get('leagueName'), data.get('teamIds'), data.get('grouping')))


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



def get_ranked_players(league_name=None, season=None):
    league_name = league_name or admin_config.get_current_league()
    if season is None:
        season = db.get_current_season(league_name)
    all_matches = db.get_matches_for_season(league_name, season)
    names = participants.resolver(league_name).names_map()

    groups = sorted(list(set([m.grouping for m in all_matches])))
    return_players = []

    for group in groups:
        group_matches = [m for m in all_matches if m.grouping == group]

        players = utility.gather_scores(group_matches)

        for player in players:
            if player['player_id'] is None:
                continue

            name = names.get(player['player_id'], player['player_id'])
            return_players.append(
                {
                    'id': player['player_id'],
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
