import copy

from backend import db, configs

SINGLES = 'SINGLES'
DOUBLES = 'DOUBLES'
FORMATS = (SINGLES, DOUBLES)
FORMAT_LOCKED_MSG = 'League format cannot change after matches exist.'
DOUBLES_MATCH_MESSAGE = ('This week, you and @partner_user play against @against_user. Please message them _today_ to find '
                         'a time that works. After your match, either of you can report the winner and score to @bot_name '
                         'in #competition_channel.')


def is_doubles(lctx):
    return lctx.configs.get(configs.LEAGUE_FORMAT) == DOUBLES


def is_doubles_league(league_name):
    return db.get_config(league_name, configs.LEAGUE_FORMAT) == DOUBLES


def set_league_format(league_name, value):
    if value not in FORMATS:
        raise ValueError('League format must be one of {}.'.format(', '.join(FORMATS)))
    if db.has_matches(league_name):
        raise ValueError(FORMAT_LOCKED_MSG)
    db.set_config(league_name, configs.LEAGUE_FORMAT, value)
    current = db.get_config(league_name, configs.MATCH_MESSAGE)
    if value == DOUBLES and current == db.DEFAULT_MATCH_MESSAGE:
        db.set_config(league_name, configs.MATCH_MESSAGE, DOUBLES_MATCH_MESSAGE)
    if value == SINGLES and current == DOUBLES_MATCH_MESSAGE:
        db.set_config(league_name, configs.MATCH_MESSAGE, db.DEFAULT_MATCH_MESSAGE)


def resolver(league_name):
    return Resolver(league_name)


class Resolver:
    """Answers identity questions about match participants. Loads the league once."""

    def __init__(self, league_name):
        self.league_name = league_name
        self.doubles = is_doubles_league(league_name)
        self.players = {p.slack_id: p for p in db.get_players(league_name)}
        self.teams = {t.team_id: t for t in db.get_all_teams(league_name)} if self.doubles else {}

    def _player_name(self, slack_id):
        player = self.players.get(slack_id)
        return player.name if player else slack_id

    def display_name(self, pid):
        if pid is None:
            return 'Bye'
        if not self.doubles:
            player = self.players.get(pid)
            return player.name if player else 'Bye'
        team = self.teams.get(pid)
        if team is None:
            return 'Bye'
        members = '{} & {}'.format(self._player_name(team.member_1), self._player_name(team.member_2))
        return '{} ({})'.format(team.name, members) if team.name else members

    def slack_ids(self, pid):
        if pid is None:
            return []
        if not self.doubles:
            return [pid]
        team = self.teams.get(pid)
        return team.members if team else []

    def tag(self, pid):
        if not self.doubles:
            return '<@{}>'.format(pid)
        team = self.teams.get(pid)
        if team is None:
            return 'Bye'
        tags = '<@{}> & <@{}>'.format(team.member_1, team.member_2)
        return '{} ({})'.format(team.name, tags) if team.name else tags

    def names_map(self):
        if not self.doubles:
            return {slack_id: p.name for slack_id, p in self.players.items()}
        return {team_id: self.display_name(team_id) for team_id in self.teams}

    def _team_for_user(self, user, season):
        for team in self.teams.values():
            if team.season == season and user in team.members:
                return team
        return None

    def participant_for_user(self, user, season):
        if not self.doubles:
            return user if user in self.players else None
        team = self._team_for_user(user, season)
        return team.team_id if team else None

    def partner_of(self, user, season):
        if not self.doubles:
            return None
        team = self._team_for_user(user, season)
        if team is None:
            return None
        return team.member_2 if team.member_1 == user else team.member_1

    def grouping_of(self, pid):
        if not self.doubles:
            player = self.players.get(pid)
            return player.grouping if player else None
        team = self.teams.get(pid)
        return team.grouping if team else None

    def participants_for_season(self, season):
        if not self.doubles:
            return [slack_id for slack_id, p in self.players.items() if p.active]
        teams = sorted([t for t in self.teams.values() if t.season == season], key=lambda t: (t.grouping or '', t.order_idx, t.team_id))
        return [t.team_id for t in teams]

    def player_view(self, matches, user):
        """Doubles: copies of the user's matches with their team id replaced by the user id. Singles: matches as-is."""
        if not self.doubles:
            return matches
        team_ids = {t.team_id for t in self.teams.values() if user in t.members}
        view = []
        for match in matches:
            if match.player_1_id not in team_ids and match.player_2_id not in team_ids:
                continue
            match_copy = copy.copy(match)
            for attr in ('player_1_id', 'player_2_id', 'winner_id'):
                if getattr(match_copy, attr) in team_ids:
                    setattr(match_copy, attr, user)
            view.append(match_copy)
        return view
