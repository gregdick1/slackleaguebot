import datetime
import random

from backend import db, configs, match_making

league_name = 'unittest'
ROSTER = [('uA', 'Alice'), ('uB', 'Bob'), ('uC', 'Carol'), ('uD', 'Dan'),
          ('uE', 'Erin'), ('uF', 'Frank'), ('uG', 'Gina'), ('uH', 'Hank'), ('uZ', 'Zed')]


def make_doubles_league(season_matches=True):
    """Doubles league, season 1: group A = AB (named) vs CD; group B = EF vs GH. Zed has no team."""
    db.set_config(league_name, configs.LEAGUE_FORMAT, 'DOUBLES')
    db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, 'comp_channel')
    db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commish')
    for slack_id, name in ROSTER:
        db.add_player(league_name, slack_id, name, '')
    teams = {
        'AB': db.add_team(league_name, 1, 'uA', 'uB', 'A', name='Bob-omb Squad'),
        'CD': db.add_team(league_name, 1, 'uC', 'uD', 'A'),
        'EF': db.add_team(league_name, 1, 'uE', 'uF', 'B'),
        'GH': db.add_team(league_name, 1, 'uG', 'uH', 'B'),
    }
    if season_matches:
        random.seed(7)
        match_making.create_matches_for_season(league_name, datetime.date(2022, 1, 3), 3, [], False)
    return teams
