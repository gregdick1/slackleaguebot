import datetime
import json

from flask import Blueprint, request, jsonify

from admin import admin_config
from backend import db, league_context

matches_api = Blueprint('matches_api', __name__)


def _get_league_context():
    lctx = league_context.LeagueContext(admin_config.get_current_league())
    return lctx


@matches_api.route('/update-match-info', methods=['POST'])
def update_match_info():
    updated_match_info = request.get_json()
    print(updated_match_info)

    lctx = _get_league_context()
    # TODO fix this jank
    updated_match_info['season'] = db.get_current_season(lctx)
    updated_match_info['sets_needed'] = 3
    db.admin_update_match(lctx, db.Match.from_dict(updated_match_info))

    return "The commissioner has spoken. The match has been updated."


@matches_api.route('/get-current-matches', methods=['GET'])
def get_current_matches():
    lctx = _get_league_context()
    season = db.get_current_season(lctx)
    current_season_matches = db.get_matches_for_season(lctx, season)
    return json.dumps(current_season_matches, default=match_player_serializer)


@matches_api.route('/get-all-players', methods=['GET'])
def get_all_players():
    league_name = request.args.get("leagueName", default="", type=str)
    lctx = league_context.LeagueContext(league_name) if league_name else _get_league_context()
    players = db.get_players(lctx)
    return json.dumps(players, default=match_player_serializer)


def match_player_serializer(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o.__dict__
