import datetime
import json

from flask import Blueprint, request

from admin import admin_config
from backend import db

matches_api = Blueprint('matches_api', __name__)


@matches_api.route('/update-match-info', methods=['POST'])
def update_match_info():
    updated_match_info = request.get_json()

    # TODO fix this jank
    league_name = admin_config.get_current_league()
    updated_match_info['season'] = db.get_current_season(league_name)
    updated_match_info['sets_needed'] = 3
    db.admin_update_match(league_name, db.Match.from_dict(updated_match_info))

    return "The commissioner has spoken. The match has been updated."


@matches_api.route('/get-current-matches', methods=['GET'])
def get_current_matches():
    # TODO pass leaguename from frontend
    league_name = admin_config.get_current_league()
    season = db.get_current_season(league_name)
    current_season_matches = db.get_matches_for_season(league_name, season)
    return json.dumps(current_season_matches, default=match_player_serializer)


@matches_api.route('/get-all-players', methods=['GET'])
def get_all_players():
    league_name = request.args.get("leagueName", default="", type=str) or admin_config.get_current_league()
    players = db.get_players(league_name)
    return json.dumps(players, default=match_player_serializer)


def match_player_serializer(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o.__dict__
