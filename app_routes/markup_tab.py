from flask import Blueprint, request, jsonify

from backend import utility
from backend.league_context import LeagueContext

markup_api = Blueprint('markup_api', __name__)


@markup_api.route('/get-league-markup', methods=['GET'])
def get_league_printout():
    league_name = request.args.get("leagueName", default="", type=str)
    if not league_name:
        return jsonify('')
    season = request.args.get("season", default=0, type=int)
    markup = utility.print_season_markup(LeagueContext.load_from_db(league_name), season)
    return jsonify(markup)

