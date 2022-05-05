import datetime
import json

from flask import Blueprint, request

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

    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        return o.__dict__
    return json.dumps(current_season_matches, default=default)
