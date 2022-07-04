import datetime
import json

from flask import Blueprint, request

from admin import admin_config
from backend import db, match_making

matches_api = Blueprint('matches_api', __name__)


@matches_api.route('/clear-score', methods=['POST'])
def clear_score():
    league_name = request.get_json().get('leagueName')
    match_id = request.get_json().get('matchId')
    db.clear_score_for_match(league_name, match_id)
    return "Success"


@matches_api.route('/set-score', methods=['POST'])
def set_score():
    league_name = request.get_json().get('leagueName')
    winner_id = request.get_json().get('winnerId')
    loser_id = request.get_json().get('loserId')
    sets = request.get_json().get('sets')
    db.update_match_by_id(league_name, winner_id, loser_id, sets)
    return "Success"


@matches_api.route('/set-forfeit', methods=['POST'])
def set_forfeit():
    league_name = request.get_json().get('leagueName')
    match_id = request.get_json().get('matchId')
    forfeit = 1 if request.get_json().get('forfeit') else 0
    db.set_match_forfeit(league_name, match_id, forfeit)
    return "Success"


@matches_api.route('/create-season', methods=['POST'])
def create_season():
    data = request.get_json()
    league_name = data.get('leagueName')
    start_date_iso = data.get('startDate')
    skip_weeks_iso = data.get('skipWeeks')
    sets_needed = data.get('setsNeeded')
    include_byes = data.get('includeByes')

    start_date = datetime.datetime.fromisoformat(start_date_iso[:-1]).date()  # Remove the Z from the end
    skip_weeks = [datetime.datetime.fromisoformat(x[:-1]).date() for x in skip_weeks_iso]  # Remove the Z from the end

    match_making.create_matches_for_season(league_name, start_date, sets_needed, skip_weeks, include_byes)
    return "Success"


@matches_api.route('/get-current-matches', methods=['GET'])
def get_current_matches():
    # TODO pass leaguename from frontend
    league_name = admin_config.get_current_league()
    season = db.get_current_season(league_name)
    current_season_matches = db.get_matches_for_season(league_name, season)
    return json.dumps(current_season_matches, default=match_player_serializer)


@matches_api.route('/get-matches-for-season', methods=['GET'])
def get_matches_for_season():
    league_name = request.args.get("leagueName", default="", type=str)
    season = request.args.get('season', default=0, type=int)
    current_season_matches = db.get_matches_for_season(league_name, season)

    organized_matches = {}
    for m in current_season_matches:
        week = m.week.isoformat()
        if m.grouping not in organized_matches:
            organized_matches[m.grouping] = {}
        if week not in organized_matches[m.grouping]:
            organized_matches[m.grouping][week] = []
        organized_matches[m.grouping][week].append(m)

    return json.dumps(organized_matches, default=match_player_serializer)


@matches_api.route('/get-all-players', methods=['GET'])
def get_all_players():
    league_name = request.args.get("leagueName", default="", type=str) or admin_config.get_current_league()
    players = db.get_players(league_name)
    return json.dumps(players, default=match_player_serializer)


def match_player_serializer(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    return o.__dict__
