import sqlite3
import os
import datetime
from functools import partial
from backend import configs

LATEST_VERSION = 3


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
              'sent INT)')

    conn.commit()
    conn.close()
    initialize_configs(league_name)


def initialize_configs(league_name):
    set_config(league_name, configs.LEAGUE_VERSION, str(LATEST_VERSION))
    set_config(league_name, configs.BOT_NAME, '@bot')
    set_config(league_name, configs.LOG_PATH, 'log.txt')
    set_config(league_name, configs.SCORE_EXAMPLE, '3-2')
    set_config(league_name, configs.MATCH_MESSAGE, 'This week, you play against @against_user. Please message them _today_ to find a time that works. After your match, report the winner and # of sets (best of 5) to @bot_name in #competition_channel.')
    set_config(league_name, configs.REMINDER_MESSAGE, 'Friendly reminder that you have a match against @against_user. Please work with them to find a time to play.')


def get_commands_to_run(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT command_id, command_text FROM commands_to_run ORDER BY command_id")
    results = c.fetchall()
    conn.commit()
    conn.close()
    return [x[1] for x in results]


_tmp_commands_to_run = {}


def add_command_to_run(league_name, command):
    if command in ['BEGIN ', 'COMMIT']:
        return
    if league_name not in _tmp_commands_to_run:
        _tmp_commands_to_run[league_name] = []
    _tmp_commands_to_run[league_name].append(command)


def save_commands_to_run(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    for command in _tmp_commands_to_run[league_name]:
        c.execute("INSERT INTO commands_to_run (command_text) VALUES (?)", (command,))
    conn.commit()
    conn.close()
    _tmp_commands_to_run[league_name] = []


def clear_commands_to_run(league_name):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("DELETE FROM commands_to_run")
    conn.commit()
    conn.close()


def set_config(league_name, name, value):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("INSERT INTO config VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value=? where name=?", (name, value, value, name))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


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
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("INSERT INTO player (slack_id, name, grouping, active) VALUES (?, ?, ?, 1)", (slack_id, name, grouping))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


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
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE player SET grouping=? WHERE slack_id = ?", (grouping, slack_id))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def updating_grouping_and_orders(league_name, slack_ids, grouping):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    for idx, slack_id in enumerate(slack_ids):
        c.execute("UPDATE player SET grouping=?, order_idx=?, active=1 WHERE slack_id = ?", (grouping, idx, slack_id))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def update_player_order_idx(league_name, slack_id, order_idx):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE player set order_idx=? WHERE slack_id = ?", (order_idx, slack_id))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def set_active(league_name, slack_id, active):
    active_int = 1 if active else 0
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE player SET active=? WHERE slack_id = ?", (active_int, slack_id))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def add_match(league_name, player_1, player_2, week_date, grouping, season, sets_needed):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()

    if player_1 is None or player_2 is None:
        p_id = player_1.slack_id if player_1 is not None else player_2.slack_id
        c.execute("INSERT INTO match (player_1, week, grouping, season, sets, sets_needed) VALUES (?, ?, ?, ?, 0, ?)", (p_id, str(week_date), grouping, season, sets_needed))
    else:
        c.execute("INSERT INTO match (player_1, player_2, week, grouping, season, sets, sets_needed) VALUES (?, ?, ?, ?, ?, 0, ?)", (player_1.slack_id, player_2.slack_id, str(week_date), grouping, season, sets_needed))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


class Match:
    def __init__(self, id, p1_id, p2_id, winner_id, week, grouping, season, sets, sets_needed, date_played, message_sent):
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

    @classmethod
    def from_db(cls, row):
        return Match(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10])

    @classmethod
    def from_dict(cls, d):
        return Match(d['id'], d['player_1_id'], d['player_2_id'], d['winner_id'], d['week'], d['grouping'], d['season'], d['sets'], d['sets_needed'])


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
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute('DELETE FROM match WHERE season = ?', (season,))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def get_matches_for_week(league_name, week):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE week = ?", (week,))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]


def get_match_by_players(league_name, player_a, player_b):
    if player_a.slack_id == player_b.slack_id:
        return None
    season = get_current_season(league_name)
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT rowid, * FROM match WHERE season = ? and (player_1 = ? or player_2 = ?) and (player_1 = ? or player_2 = ?)",
              (season, player_a.slack_id, player_a.slack_id, player_b.slack_id, player_b.slack_id))
    row = c.fetchone()
    conn.close()

    if row is None or len(row) == 0:
        print("No match for players:", player_a.name, player_b.name)
        return None
    return Match.from_db(row)


def update_match(league_name, winner_name, loser_name, sets):
    winner = get_player_by_name(league_name, winner_name)
    loser = get_player_by_name(league_name, loser_name)
    return _update_match(league_name, winner, loser, sets)


def update_match_by_id(league_name, winner_id, loser_id, sets):
    winner = get_player_by_id(league_name, winner_id)
    loser = get_player_by_id(league_name, loser_id)
    return _update_match(league_name, winner, loser, sets)


def _update_match(league_name, winner, loser, sets):
    if winner is None or loser is None:
        print('Could not update match')
        return False

    match = get_match_by_players(league_name, winner, loser)
    if match is None:
        print('Could not update match')
        return False

    if sets < match.sets_needed or sets > (match.sets_needed*2-1):
        print('Sets out of range, was {}, but must be between {} and {}'.format(sets, match.sets_needed, match.sets_needed*2-1))
        return False

    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE match SET winner=?, sets=?, date_played=? WHERE player_1 = ? and player_2 = ? and season=?", (winner.slack_id, sets, str(datetime.date.today()), match.player_1_id, match.player_2_id, match.season))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)
    return True


def admin_update_match(league_name, new_match):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE match SET player_1=?, player_2=?, winner=?, week=?, grouping=?, sets=?, sets_needed=?, date_played=?, message_sent=? WHERE rowid=?",
              (new_match.player_1_id, new_match.player_2_id, new_match.winner_id, new_match.week, new_match.grouping, new_match.sets, new_match.sets_needed, new_match.date_played, new_match.message_sent, new_match.id))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)
    return True


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


def add_reminder_day(league_name, date):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("INSERT INTO reminder_days (date, sent) VALUES (?, 0)", (date,))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def remove_reminder_day(league_name, date):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("DELETE FROM reminder_days WHERE date=?", (date,))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def mark_reminder_day_sent(league_name, date):
    conn = get_connection(league_name)
    conn.set_trace_callback(partial(add_command_to_run, league_name))
    c = conn.cursor()
    c.execute("UPDATE reminder_days SET sent=1 WHERE date=?", (date,))
    conn.commit()
    conn.close()
    save_commands_to_run(league_name)


def get_reminder_days_since(league_name, date):
    conn = get_connection(league_name)
    c = conn.cursor()
    c.execute("SELECT * FROM reminder_days WHERE date >= ?", (date,))
    rows = c.fetchall()
    conn.commit()
    conn.close()
    if rows is None or len(rows) == 0:
        return []
    reminder_dates = [{'date': x[0], 'sent': x[1]} for x in rows]
    reminder_dates = sorted(reminder_dates, key=lambda d: d['date'])
    return reminder_dates
