import sqlite3
import os
import datetime
from functools import partial
from backend import configs

LATEST_VERSION = 7

DEFAULT_MATCH_MESSAGE = 'This week, you play against @against_user. Please message them _today_ to find a time that works. After your match, report the winner and # of sets (best of 5) to @bot_name in #competition_channel.'

TEAM_TABLE_DDL = ('CREATE TABLE team ('
                  'team_id TEXT PRIMARY KEY, '
                  'season INT NOT NULL, '
                  'name TEXT, '
                  'member_1 TEXT NOT NULL, '
                  'member_2 TEXT NOT NULL, '
                  'grouping TEXT, '
                  'order_idx INT DEFAULT 0, '
                  'FOREIGN KEY (member_1) REFERENCES player, '
                  'FOREIGN KEY (member_2) REFERENCES player)')


def path(league_name):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../{}_league.sqlite".format(league_name)))


def get_connection(league_name):
    return sqlite3.connect(path(league_name), detect_types=sqlite3.PARSE_DECLTYPES)


def initialize(league_name):
    if os.path.exists(path(league_name)):
        return

    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute('CREATE TABLE player ('
              'slack_id TEXT PRIMARY KEY, '
              'name TEXT, '
              'grouping TEXT, '
              'active INT, '
              'order_idx INT DEFAULT 0)')
    c.execute('CREATE TABLE match ('
              'player_1 TEXT, '
              'player_2 TEXT, '
              'winner TEXT, '
              'week DATE, '
              'grouping TEXT, '
              'season INT, '
              'sets INT, '
              'sets_needed INT, '
              'date_played DATE, '
              'message_sent INT DEFAULT 0, '
              'forfeit INT DEFAULT 0, '
              'player_1_score INT, '
              'player_2_score INT, '
              'tie_score INT, '
              'play_all_sets DEFAULT 0, '
              'FOREIGN KEY (player_1) REFERENCES player, '
              'FOREIGN KEY (player_2) REFERENCES player, '
              'FOREIGN KEY (winner) REFERENCES player)')
    c.execute('CREATE TABLE config ('
              'name TEXT PRIMARY KEY, '
              'value TEXT)')
    c.execute('CREATE TABLE commands_to_run ('
              'command_id INTEGER PRIMARY KEY AUTOINCREMENT, '
              'command_text text NOT NULL)')
    c.execute('CREATE TABLE reminder_days ('
              'date DATE, '
              'sent INT, '
              'season INT DEFAULT 0)')
    c.execute(TEAM_TABLE_DDL)

    conn.commit()
    conn.close()
    initialize_configs(league_name)


def initialize_configs(league_name):
    set_config(league_name, configs.LEAGUE_VERSION, str(LATEST_VERSION))
    set_config(league_name, configs.BOT_NAME, '@bot')
    set_config(league_name, configs.LOG_PATH, 'log.txt')
    set_config(league_name, configs.SCORE_EXAMPLE, '3-2')
    set_config(league_name, configs.MATCH_MESSAGE, DEFAULT_MATCH_MESSAGE)
    set_config(league_name, configs.REMINDER_MESSAGE, 'Friendly reminder that you have a match against @against_user. Please work with them to find a time to play.')
    set_config(league_name, configs.LEAGUE_FORMAT, 'SINGLES')


_tmp_commands_to_run = {}


def add_command_to_run(league_name, command):
    if command in ['BEGIN ', 'COMMIT']:
        return
    if league_name not in _tmp_commands_to_run:
        _tmp_commands_to_run[league_name] = []
    _tmp_commands_to_run[league_name].append(command)


def clear_tmp_commands_to_run(league_name):
    _tmp_commands_to_run[league_name] = []


def _execute_write(league_name, work):
    conn = get_connection(league_name)
    try:
        conn.set_trace_callback(partial(add_command_to_run, league_name))
        result = work(conn.cursor())
        conn.commit()
        conn.close()
        save_commands_to_run(league_name)
        return result
    except Exception:
        clear_tmp_commands_to_run(league_name)
        raise
    finally:
        conn.close()


def get_commands_to_run(league_name):
    conn = get_connection(league_name)
    try:
        c = conn.cursor()
        c.execute("SELECT command_id, command_text FROM commands_to_run ORDER BY command_id")
        return [x[1] for x in c.fetchall()]
    finally:
        conn.close()


def save_commands_to_run(league_name):
    conn = get_connection(league_name)
    try:
        c = conn.cursor()
        for command in _tmp_commands_to_run.get(league_name, []):
            c.execute("INSERT INTO commands_to_run (command_text) VALUES (?)", (command,))
        conn.commit()
    finally:
        conn.close()
    _tmp_commands_to_run[league_name] = []


def clear_commands_to_run(league_name):
    conn = get_connection(league_name)
    try:
        conn.cursor().execute("DELETE FROM commands_to_run")
        conn.commit()
    finally:
        conn.close()


def set_config(league_name, name, value):
    _execute_write(league_name, lambda c: c.execute(
        "INSERT INTO config VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value=? where name=?", (name, value, value, name)))


def get_config(league_name, name):
    initialize(league_name)
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE name = ?", (name,))
    rows = c.fetchall()
    conn.close()
    if rows:
        return rows[0][0]
    return None


def add_player(league_name, slack_id, name, grouping):
    _execute_write(league_name, lambda c: c.execute(
        "INSERT INTO player (slack_id, name, grouping, active) VALUES (?, ?, ?, 1)", (slack_id, name, grouping)))


class Player:
    def __init__(self, slack_id, name, grouping, active, order_idx):
        self.slack_id = slack_id
        self.name = name
        self.grouping = grouping
        self.active = active
        self.order_idx = order_idx

    @classmethod
    def from_db(cls, row):
        return Player(row[0], row[1], row[2], row[3], row[4])

    def __str__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.grouping + ' ' + str(self.active)

    def __repr__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.grouping + ' ' + str(self.active)

    def __eq__(self, other):
        if other is None:
            return False
        return self.slack_id == other.slack_id and self.name == other.name


def get_players(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute('SELECT * FROM player')
    rows = c.fetchall()
    conn.close()
    return [Player.from_db(p) for p in rows]


def get_active_players(league_name):
    return [p for p in get_players(league_name) if p.active]


def get_player_by_name(league_name, name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Could not find player with name:', name)
        return None
    return Player.from_db(row)


def get_player_by_id(league_name, id):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE slack_id = ?", (id,))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Could not find player with id:', id)
        return None
    return Player.from_db(row)


def update_grouping(league_name, slack_id, grouping):
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE player SET grouping=? WHERE slack_id = ?", (grouping, slack_id)))


def updating_grouping_and_orders(league_name, slack_ids, grouping):
    def work(c):
        for idx, slack_id in enumerate(slack_ids):
            c.execute("UPDATE player SET grouping=?, order_idx=?, active=1 WHERE slack_id = ?", (grouping, idx, slack_id))
    _execute_write(league_name, work)


def update_player_order_idx(league_name, slack_id, order_idx):
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE player set order_idx=? WHERE slack_id = ?", (order_idx, slack_id)))


def set_active(league_name, slack_id, active):
    active_int = 1 if active else 0
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE player SET active=? WHERE slack_id = ?", (active_int, slack_id)))


TEAM_NAME_ERROR = "Team names can't contain | < > or line breaks, and must be 40 characters or fewer."
TEAM_COLUMNS = 'team_id, season, name, member_1, member_2, grouping, order_idx'


class Team:
    def __init__(self, team_id, season, name, member_1, member_2, grouping, order_idx):
        self.team_id = team_id
        self.season = season
        self.name = name
        self.member_1 = member_1
        self.member_2 = member_2
        self.grouping = grouping
        self.order_idx = order_idx

    @property
    def members(self):
        return [self.member_1, self.member_2]

    @classmethod
    def from_db(cls, row):
        return Team(*row)


def _clean_team_name(name):
    if name is None or not name.strip():
        return None
    name = name.strip()
    if len(name) > 40 or any(ch in name for ch in '|<>\n\r'):
        raise ValueError(TEAM_NAME_ERROR)
    return name


def _query_teams(league_name, where='', params=()):
    conn = get_connection(league_name)
    try:
        rows = conn.cursor().execute('SELECT {} FROM team {} ORDER BY season, grouping, order_idx, team_id'.format(TEAM_COLUMNS, where), params).fetchall()
    finally:
        conn.close()
    return [Team.from_db(r) for r in rows]


def get_all_teams(league_name):
    return _query_teams(league_name)


def get_teams_for_season(league_name, season):
    return _query_teams(league_name, 'WHERE season = ?', (season,))


def get_team_by_id(league_name, team_id):
    teams = _query_teams(league_name, 'WHERE team_id = ?', (team_id,))
    return teams[0] if teams else None


def get_team_for_user(league_name, slack_id, season):
    teams = _query_teams(league_name, 'WHERE season = ? AND (member_1 = ? OR member_2 = ?)', (season, slack_id, slack_id))
    return teams[0] if teams else None


def _validate_members(league_name, season, member_1, member_2, ignore_team_id=None):
    if member_1 == member_2:
        raise ValueError('A team needs two different players.')
    names = {p.slack_id: p.name for p in get_players(league_name)}
    for m in (member_1, member_2):
        if m not in names:
            raise ValueError('{} is not a player in this league.'.format(m))
    for team in get_teams_for_season(league_name, season):
        if team.team_id == ignore_team_id:
            continue
        for m in (member_1, member_2):
            if m in team.members:
                raise ValueError('{} is already on a team for season {}.'.format(names[m], season))


def add_team(league_name, season, member_1, member_2, grouping, name=None):
    name = _clean_team_name(name)
    _validate_members(league_name, season, member_1, member_2)
    existing = get_teams_for_season(league_name, season)
    n = 1 + max([int(t.team_id.split('-')[1]) for t in existing] + [0])
    team_id = 'T{}-{}'.format(season, n)
    order_idx = len([t for t in existing if t.grouping == grouping])
    _execute_write(league_name, lambda c: c.execute(
        'INSERT INTO team (team_id, season, name, member_1, member_2, grouping, order_idx) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (team_id, season, name, member_1, member_2, grouping, order_idx)))
    return team_id


_UNSET = object()


def update_team(league_name, team_id, name=_UNSET, member_1=None, member_2=None):
    team = get_team_by_id(league_name, team_id)
    if team is None:
        raise ValueError('No team {}.'.format(team_id))
    new_name = team.name if name is _UNSET else _clean_team_name(name)
    new_1 = member_1 or team.member_1
    new_2 = member_2 or team.member_2
    members_changing = new_1 != team.member_1 or new_2 != team.member_2
    if members_changing and _team_has_matches(league_name, team_id):
        raise ValueError('Team {} has matches; members cannot be changed.'.format(team_id))
    _validate_members(league_name, team.season, new_1, new_2, ignore_team_id=team_id)
    _execute_write(league_name, lambda c: c.execute(
        'UPDATE team SET name=?, member_1=?, member_2=? WHERE team_id=?', (new_name, new_1, new_2, team_id)))


def _team_has_matches(league_name, team_id):
    conn = get_connection(league_name)
    try:
        return conn.cursor().execute(
            'SELECT 1 FROM match WHERE player_1 = ? OR player_2 = ? OR winner = ? LIMIT 1',
            (team_id, team_id, team_id)).fetchone() is not None
    finally:
        conn.close()


def delete_team(league_name, team_id):
    if _team_has_matches(league_name, team_id):
        raise ValueError('Team {} has matches and cannot be deleted.'.format(team_id))
    _execute_write(league_name, lambda c: c.execute('DELETE FROM team WHERE team_id = ?', (team_id,)))


def update_team_grouping_and_orders(league_name, team_ids, grouping):
    def work(c):
        for idx, team_id in enumerate(team_ids):
            c.execute('UPDATE team SET grouping=?, order_idx=? WHERE team_id=?', (grouping, idx, team_id))
    _execute_write(league_name, work)


def has_matches(league_name):
    conn = get_connection(league_name)
    try:
        return conn.cursor().execute('SELECT 1 FROM match LIMIT 1').fetchone() is not None
    finally:
        conn.close()


def add_match(league_name, player_1, player_2, week_date, grouping, season, sets_needed, play_all_sets=0):
    add_match_by_ids(league_name,
                     player_1.slack_id if player_1 is not None else None,
                     player_2.slack_id if player_2 is not None else None,
                     week_date, grouping, season, sets_needed, play_all_sets)


def add_match_by_ids(league_name, p1_id, p2_id, week_date, grouping, season, sets_needed, play_all_sets=0):
    if p1_id is None and p2_id is None:
        raise ValueError('A match needs at least one participant.')

    def work(c):
        if p1_id is None or p2_id is None:
            p_id = p1_id if p1_id is not None else p2_id
            c.execute("INSERT INTO match (player_1, week, grouping, season, sets, sets_needed, play_all_sets, player_1_score, player_2_score, tie_score) VALUES (?, ?, ?, ?, 0, ?, ?, 0, 0, 0)", (p_id, str(week_date), grouping, season, sets_needed, play_all_sets))
        else:
            c.execute("INSERT INTO match (player_1, player_2, week, grouping, season, sets, sets_needed, play_all_sets, player_1_score, player_2_score, tie_score) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 0, 0, 0)", (p1_id, p2_id, str(week_date), grouping, season, sets_needed, play_all_sets))
    _execute_write(league_name, work)


class Match:
    def __init__(self, id, p1_id, p2_id, winner_id, week, grouping, season, sets, sets_needed, date_played, message_sent, forfeit, p1_score, p2_score, tie_score, play_all_sets):
        self.id = id
        self.player_1_id = p1_id
        self.player_2_id = p2_id
        self.winner_id = winner_id
        self.week = week
        self.grouping = grouping
        self.season = season
        self.sets = sets
        self.sets_needed = sets_needed
        self.date_played = date_played
        self.message_sent = message_sent
        self.forfeit = forfeit
        self.player_1_score = p1_score
        self.player_2_score = p2_score
        self.tie_score = tie_score
        self.play_all_sets = play_all_sets

    @classmethod
    def from_db(cls, row):
        return Match(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15])


def get_matches(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute('SELECT rowid, * FROM match')
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def get_matches_for_season(league_name, season):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute('SELECT rowid, * FROM match WHERE season = ?', (season,))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def clear_matches_for_season(league_name, season):
    _execute_write(league_name, lambda c: c.execute('DELETE FROM match WHERE season = ?', (season,)))


def get_matches_for_week(league_name, week):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE week = ?", (week,))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def get_match_by_players(league_name, player_a, player_b):
    return get_match_by_participants(league_name, player_a.slack_id, player_b.slack_id)


def get_match_by_participants(league_name, a_id, b_id):
    if a_id == b_id:
        return None
    season = get_current_season(league_name)
    conn = get_connection(league_name)
    try:
        row = conn.cursor().execute(
            "SELECT rowid, * FROM match WHERE season = ? and (player_1 = ? or player_2 = ?) and (player_1 = ? or player_2 = ?)",
            (season, a_id, a_id, b_id, b_id)).fetchone()
    finally:
        conn.close()
    if row is None or len(row) == 0:
        print("No match for participants:", a_id, b_id)
        return None
    return Match.from_db(row)


def get_match_by_id(league_name, id):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE rowid = ?", (id,))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Could not find match with id:', id)
        return None
    return Match.from_db(row)


def update_match(league_name, winner_name, loser_name, winner_score, loser_score, tie_score):
    winner = get_player_by_name(league_name, winner_name)
    loser = get_player_by_name(league_name, loser_name)
    return _update_match(league_name, winner, loser, winner_score, loser_score, tie_score)


def update_match_by_id(league_name, winner_id, loser_id, winner_score, loser_score, tie_score):
    winner = get_player_by_id(league_name, winner_id)
    loser = get_player_by_id(league_name, loser_id)
    return _update_match(league_name, winner, loser, winner_score, loser_score, tie_score)


def _update_match(league_name, winner, loser, winner_score, loser_score, tie_score):
    if winner is None or loser is None:
        print('Could not update match')
        return False
    return update_match_by_participants(league_name, winner.slack_id, loser.slack_id, winner_score, loser_score, tie_score)


def update_match_by_participants(league_name, winner_id, loser_id, winner_score, loser_score, tie_score):
    match = get_match_by_participants(league_name, winner_id, loser_id)
    if match is None:
        print('Could not update match')
        return False

    sets = winner_score + loser_score + tie_score

    if match.play_all_sets:
        if sets != match.sets_needed:
            print('Sets out of range, was {}, but must be {}'.format(sets, match.sets_needed))
            return False
    else:
        if sets < match.sets_needed or sets > (match.sets_needed * 2 - 1):
            print('Sets out of range, was {}, but must be between {} and {}'.format(sets, match.sets_needed, match.sets_needed * 2 - 1))
            return False

    p1_score = winner_score if winner_id == match.player_1_id else loser_score
    p2_score = winner_score if winner_id == match.player_2_id else loser_score

    _execute_write(league_name, lambda c: c.execute(
        "UPDATE match SET winner=?, player_1_score=?, player_2_score=?, tie_score=?, sets=?, date_played=? WHERE player_1 = ? and player_2 = ? and season=?",
        (winner_id, p1_score, p2_score, tie_score, sets, str(datetime.date.today()), match.player_1_id, match.player_2_id, match.season)))
    return True


def clear_score_for_match(league_name, match_id):
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE match SET winner=?, sets=?, player_1_score=?, player_2_score=?, tie_score=?, date_played=? WHERE rowid=?", (None, 0, 0, 0, 0, None, match_id)))


def mark_match_message_sent(league_name, match_id, sent=1):
    _execute_write(league_name, lambda c: c.execute("UPDATE match SET message_sent=? WHERE rowid=?", (sent, match_id)))


def set_match_forfeit(league_name, match_id, forfeit=1):
    _execute_write(league_name, lambda c: c.execute("UPDATE match SET forfeit=? WHERE rowid=?", (forfeit, match_id)))


def admin_update_match_score(league_name, match_id, winner_id, winner_score, loser_score, tie_score):
    match = get_match_by_id(league_name, match_id)
    if match is None:
        return False
    p1_score = winner_score if winner_id == match.player_1_id else loser_score
    p2_score = winner_score if winner_id == match.player_2_id else loser_score
    sets = p1_score + p2_score + tie_score
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE match SET winner=?, player_1_score=?, player_2_score=?, tie_score=?, sets=? WHERE rowid=?",
        (winner_id, p1_score, p2_score, tie_score, sets, match_id)))
    return True


def update_match_players(league_name, match_id, player_1_id, player_2_id):
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE match SET player_1=?, player_2=? WHERE rowid=?", (player_1_id, player_2_id, match_id)))


def get_current_season(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT MAX(season) FROM match")
    rows = c.fetchall()
    conn.close()
    current_season = rows[0][0]
    if current_season is None:
        return 0
    return current_season


def get_all_seasons(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT distinct season FROM match")
    rows = c.fetchall()
    conn.close()
    if rows is None or len(rows) == 0:
        return []
    seasons = [x[0] for x in rows]
    seasons.sort()
    return seasons


def add_reminder_day(league_name, season, date):
    _execute_write(league_name, lambda c: c.execute(
        "INSERT INTO reminder_days (date, season, sent) VALUES (?,?,0)", (date, season)))


def remove_reminder_day(league_name, season, date):
    _execute_write(league_name, lambda c: c.execute(
        "DELETE FROM reminder_days WHERE date=? and season=?", (date, season)))


def mark_reminder_day_sent(league_name, season, date):
    _execute_write(league_name, lambda c: c.execute(
        "UPDATE reminder_days SET sent=1 WHERE date=? and season=?", (date, season)))


def get_reminder_days_for_season(league_name, season):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT date, sent, season FROM reminder_days WHERE season = ?", (season,))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    if rows is None or len(rows) == 0:
        return []
    reminder_dates = [{'date': x[0], 'sent': x[1], 'season': x[2]} for x in rows]
    reminder_dates = sorted(reminder_dates, key=lambda d: d['date'])
    return reminder_dates


def get_reminder_days_since(league_name, season, date):
    reminder_days = get_reminder_days_for_season(league_name, season)
    return [x for x in reminder_days if x['date'] >= date]
