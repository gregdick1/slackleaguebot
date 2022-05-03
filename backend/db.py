import sqlite3
import datetime
import os


def path(lctx):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../{}_league.sqlite".format(lctx.league_name)))


def get_connection(lctx):
    return sqlite3.connect(path(lctx), detect_types=sqlite3.PARSE_DECLTYPES)


def initialize(lctx):
    if os.path.exists(path(lctx)):
        return
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute('CREATE TABLE player (slack_id TEXT PRIMARY KEY, name TEXT, grouping TEXT, active INT)')
    c.execute('CREATE TABLE match ('
              'player_1 TEXT, '
              'player_2 TEXT, '
              'winner TEXT, '
              'week DATE, '
              'grouping TEXT, '
              'season INT, '
              'sets INT, '
              'sets_needed INT, '
              'FOREIGN KEY (player_1) REFERENCES player, '
              'FOREIGN KEY (player_2) REFERENCES player, '
              'FOREIGN KEY (winner) REFERENCES player)')
    c.execute('CREATE TABLE config ('
              'name TEXT PRIMARY KEY, '
              'value TEXT)')

    conn.commit()
    conn.close()


def set_config(lctx, name, value):
    conn = get_connection(lctx)
    c = conn.cursor()

    c.execute("INSERT INTO config VALUES ('{}', '{}') "
              "ON CONFLICT(name) DO UPDATE SET value='{}' where name='{}'".format(name, value, value, name))
    conn.commit()
    conn.close()


def get_config(lctx, name):
    initialize(lctx)
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE name = '{}'".format(name))
    rows = c.fetchall()
    conn.close()
    if rows:
        return rows[0][0]
    return None


def add_player(lctx, slack_id, name, grouping):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("INSERT INTO player VALUES ('{}', '{}', '{}', 1)".format(slack_id, name.replace("'","''"), grouping))
    conn.commit()
    conn.close()


class Player:
    def __init__(self, slack_id, name, grouping, active):
        self.slack_id = slack_id
        self.name = name
        self.grouping = grouping
        self.active = active

    @classmethod
    def from_db(cls, row):
        return Player(row[0], row[1], row[2], row[3])

    def __str__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.grouping + ' ' + str(self.active)

    def __repr__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.grouping + ' ' + str(self.active)


def get_players(lctx):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute('SELECT * FROM player')
    rows = c.fetchall()
    conn.close()
    return [Player.from_db(p) for p in rows]


def get_active_players(lctx):
    return [p for p in get_players(lctx) if p.active]


def get_player_by_name(lctx, name):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE name = '{}'".format(name))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Could not find player with name:', name)
        return None
    return Player.from_db(row)


def get_player_by_id(lctx, id):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE slack_id = '{}'".format(id))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Could not find player with id:', id)
        return None
    return Player.from_db(row)


def update_grouping(lctx, slack_id, grouping):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("UPDATE player SET grouping='{}' WHERE slack_id = '{}'".format(grouping, slack_id))
    conn.commit()
    conn.close()


def set_active(lctx, slack_id, active):
    conn = get_connection(lctx)
    c = conn.cursor()
    active_int = 1 if active else 0
    c.execute("UPDATE player SET active={} WHERE slack_id = '{}'".format(active_int, slack_id))
    conn.commit()
    conn.close()


def add_match(lctx, player_1, player_2, week_date, grouping, season, sets_needed):
    conn = get_connection(lctx)
    c = conn.cursor()
    if player_1 is None or player_2 is None:
        p_id = player_1.slack_id if player_1 is not None else player_2.slack_id
        c.execute("INSERT INTO match VALUES ('{}', null, null, '{}', '{}', {}, 0, {})".format(p_id, str(week_date), grouping, season, sets_needed))
    else:
        c.execute("INSERT INTO match VALUES ('{}', '{}', null, '{}', '{}', {}, 0, {})".format(player_1.slack_id, player_2.slack_id, str(week_date), grouping, season, sets_needed))
    conn.commit()
    conn.close()


class Match:
    def __init__(self, id, p1_id, p2_id, winner_id, week, grouping, season, sets, sets_needed):
        self.id = id
        self.player_1_id = p1_id
        self.player_2_id = p2_id
        self.winner_id = winner_id
        self.week = week
        self.grouping = grouping
        self.season = season
        self.sets = sets
        self.sets_needed = sets_needed

    @classmethod
    def from_db(cls, row):
        return Match(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])


def get_matches(lctx):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute('SELECT rowid, * FROM match')
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def get_matches_for_season(lctx, season):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute('SELECT rowid, * FROM match WHERE season = {}'.format(season))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def clear_matches_for_season(lctx, season):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute('DELETE FROM match WHERE season = {}'.format(season))
    conn.commit()
    conn.close()


def get_matches_for_week(lctx, week):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE week = '{}'".format(week))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def get_match_by_players(lctx, player_a, player_b):
    if player_a.slack_id == player_b.slack_id:
        return None
    season = get_current_season(lctx)
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE season = {} and (player_1 = '{}' or player_2 = '{}') and (player_1 = '{}' or player_2 = '{}')"\
              .format(season, player_a.slack_id, player_a.slack_id, player_b.slack_id, player_b.slack_id))
    row = c.fetchone()
    conn.close()

    if row is None or len(row) == 0:
        print("No match for players:", player_a.name, player_b.name)
        return None
    return Match.from_db(row)


def update_match(lctx, winner_name, loser_name, sets):
    winner = get_player_by_name(lctx, winner_name)
    loser = get_player_by_name(lctx, loser_name)
    return _update_match(lctx, winner, loser, sets)


def update_match_by_id(lctx, winner_id, loser_id, sets):
    winner = get_player_by_id(lctx, winner_id)
    loser = get_player_by_id(lctx, loser_id)
    return _update_match(lctx, winner, loser, sets)


def _update_match(lctx, winner, loser, sets):
    if winner is None or loser is None:
        print('Could not update match')
        return False

    match = get_match_by_players(lctx, winner, loser)
    if match is None:
        print('Could not update match')
        return False

    if sets < match.sets_needed or sets > (match.sets_needed*2-1):
        print('Sets out of range, was {}, but must be between {} and {}'.format(sets, match.sets_needed, match.sets_needed*2-1))
        return False

    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("UPDATE match SET winner='{}', sets={} WHERE player_1 = '{}' and player_2 = '{}' and season={}"\
              .format(winner.slack_id, sets, match.player_1_id, match.player_2_id, match.season))
    conn.commit()
    conn.close()
    return True


def admin_update_match(lctx, new_match):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("UPDATE match SET " +
              "player_1='{}', ".format(new_match.player_1_id) +
              "player_2='{}', ".format(new_match.player_2_id) +
              ("winner='{}', ".format(new_match.winner_id) if new_match.winner_id is not None else "winner=null, ") +
              "week='{}', ".format(new_match.week) +
              "grouping='{}', ".format(new_match.grouping) +
              "sets={}, ".format(new_match.sets) +
              "sets_needed={} ".format(new_match.sets_needed) +
              "WHERE rowid={}".format(new_match.id))
    conn.commit()
    conn.close()
    return True


def get_current_season(lctx):
    conn = get_connection(lctx)
    c = conn.cursor()
    c.execute("SELECT MAX(season) FROM match")
    rows = c.fetchall()
    conn.close()
    current_season = rows[0][0]
    if current_season is None:
        return 0
    return current_season
