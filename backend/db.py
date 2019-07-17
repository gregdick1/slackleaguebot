import sqlite3
import datetime
import os
import subprocess

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../smash_league.sqlite"))

command_prefix = ''
command_suffix = ''
if True: #windows
    command_prefix = '"C:\Program Files\Git\\bin\\bash.exe" -c "'
    command_suffix = '"'
def get_connection():
    return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

def push_db():
    p = subprocess.Popen(command_prefix+'cp smash_league.sqlite smash_league.sqlite.bak'+command_suffix, shell=True).wait()
    p = subprocess.Popen(command_prefix+'rsync -avzhe ssh smash_league.sqlite ec2-user@10.110.83.255:~/smashbot/'+command_suffix, shell=True).wait()
    p = subprocess.Popen(command_prefix+'rm smash_league.sqlite'+command_suffix, shell=True).wait()

def rm_db():
    p = subprocess.Popen(command_prefix+'rm smash_league.sqlite'+command_suffix, shell=True).wait()

def create_tables():
    # Connecting to the database file
    conn = get_connection()
    c = conn.cursor()

    c.execute('CREATE TABLE player (slack_id TEXT PRIMARY KEY, name TEXT, grouping TEXT, active INT)')

    # Creating a second table with 1 column and set it as PRIMARY KEY
    # note that PRIMARY KEY column must consist of unique values!
    c.execute('CREATE TABLE match ('
              'player_1 TEXT, '
              'player_2 TEXT, '
              'winner TEXT, '
              'week DATE, '
              'grouping TEXT, '
              'season INT, '
              'sets INT, '
              'FOREIGN KEY (player_1) REFERENCES player, '
              'FOREIGN KEY (player_2) REFERENCES player, '
              'FOREIGN KEY (winner) REFERENCES player)')

    # Committing changes and closing the connection to the database file
    conn.commit()
    conn.close()

def create_floor_battle_tables():
    conn = get_connection()
    c = conn.cursor()

    c.execute('CREATE TABLE floor_player (slack_id TEXT PRIMARY KEY, name TEXT, floor TEXT)')
    c.execute('CREATE TABLE floor_match ('
              'winner TEXT, '
              'loser TEXT, '
              'sets INT, '
              'FOREIGN KEY (winner) REFERENCES floor_player, '
              'FOREIGN KEY (loser) REFERENCES floor_player)')
    conn.commit()
    conn.close()

def add_player(slack_id, name, grouping):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO player VALUES ('{}', '{}', '{}', 1)".format(slack_id, name.replace("'","''"), grouping))
    conn.commit()
    conn.close()

def add_floor_player(slack_id, name, floor):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO floor_player VALUES ('{}', '{}', '{}')".format(slack_id, name, floor))
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

class FloorPlayer:
    def __init__(self, slack_id, name, floor):
        self.slack_id = slack_id
        self.name = name
        self.floor = floor

    @classmethod
    def from_db(cls, row):
        return FloorPlayer(row[0], row[1], row[2])

    def __str__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.floor + ' '

    def __repr__(self):
        return self.name + ' ' + self.slack_id + ' ' + self.floor + ' '

def get_players():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM player')
    rows = c.fetchall()
    conn.close()

    return [Player.from_db(p) for p in rows]

def get_floor_players():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM floor_player')
    rows = c.fetchall()
    conn.close()

    return [FloorPlayer.from_db(p) for p in rows]

def get_active_players():
    return [p for p in get_players() if p.active]

def get_player_by_name(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE name = '{}'".format(name))
    row = c.fetchone()
    conn.close()
    if row is None or len(row) == 0:
        print('Couldn not find player with name:', name)
        return None
    return Player.from_db(row)

def get_player_by_id(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM player WHERE slack_id = '{}'".format(id))
    row = c.fetchone()
    conn.close()
    if len(row) == 0:
        print('Couldn not find player with id:', id)
        return None
    return Player.from_db(row)

def get_floor_player_by_id(id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM floor_player WHERE slack_id = '{}'".format(id))
    row = c.fetchone()
    conn.close()
    if row == None or len(row) == 0:
        print('Could not find player with id:', id)
        return None
    return FloorPlayer.from_db(row)

def set_floor_for_player(slack_id, floor):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE floor_player SET floor = '{}' WHERE slack_id = '{}'".format(floor, slack_id))
    conn.commit()
    conn.close()

def update_grouping(slack_id, grouping):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE player SET grouping='{}' WHERE slack_id = '{}'".format(grouping, slack_id))
    conn.commit()
    conn.close()

def set_active(slack_id, active):
    conn = get_connection()
    c = conn.cursor()
    active_int = 1 if active else 0
    c.execute("UPDATE player SET active={} WHERE slack_id = '{}'".format(active_int, slack_id))
    conn.commit()
    conn.close()

def add_match(player_1, player_2, week_date, grouping, season):
    conn = get_connection()
    c = conn.cursor()
    if player_1 is None or player_2 is None:
        p_id = player_1.slack_id if player_1 is not None else player_2.slack_id
        c.execute("INSERT INTO match VALUES ('{}', null, null, '{}', '{}', {}, 0)".format(p_id, str(week_date), grouping, season))
    else:
        c.execute("INSERT INTO match VALUES ('{}', '{}', null, '{}', '{}', {}, 0)".format(player_1.slack_id, player_2.slack_id, str(week_date), grouping, season))
    conn.commit()
    conn.close()

def add_floor_match(winner_id, loser_id, sets):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO floor_match VALUES ('{}', '{}', {})".format(winner_id, loser_id, sets))
    conn.commit()
    conn.close()
    return True

class Match:
    def __init__(self, p1_id, p2_id, winner_id, week, grouping, season, sets):
        self.player_1_id = p1_id
        self.player_2_id = p2_id
        self.winner_id = winner_id
        self.week = week
        self.grouping = grouping
        self.season = season
        self.sets = sets

    @classmethod
    def from_db(cls, row):
        return Match(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

class FloorMatch:
    def __init__(self, winner_id, loser_id, sets):
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.sets = sets

    @classmethod
    def from_db(cls, row):
        return FloorMatch(row[0], row[1], row[2])

def get_floor_matches():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM floor_match')
    rows = c.fetchall()
    conn.close()
    return [FloorMatch.from_db(m) for m in rows]

def get_matches():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM match')
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]

def get_matches_for_season(season):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM match WHERE season = {}'.format(season))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]

def clear_matches_for_season(season):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM match WHERE season = {}'.format(season))
    conn.commit()
    conn.close()

def get_matches_for_week(week):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM match WHERE week = '{}'".format(week))
    rows = c.fetchall()
    conn.close()

    return [Match.from_db(m) for m in rows]

def get_match_by_players(player_a, player_b):
    season = get_current_season()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM match WHERE season = {} and (player_1 = '{}' or player_2 = '{}') and (player_1 = '{}' or player_2 = '{}')"\
              .format(season, player_a.slack_id, player_a.slack_id, player_b.slack_id, player_b.slack_id))
    row = c.fetchone()
    conn.close()

    if len(row) == 0:
        print("No match for players:", player_a.name, player_b.name)
        return None
    return Match.from_db(row)

def update_match(winner_name, loser_name, sets):
    winner = get_player_by_name(winner_name)
    loser = get_player_by_name(loser_name)
    return _update_match(winner, loser, sets)

def update_match_by_id(winner_id, loser_id, sets):
    winner = get_player_by_id(winner_id)
    loser = get_player_by_id(loser_id)
    return _update_match(winner, loser, sets)

def _update_match(winner, loser, sets):
    if winner is None or loser is None:
        print('Could not update match')
        return False

    if sets not in [2,3]:
        print('Sets must be 2 or 3')
        return False

    match = get_match_by_players(winner, loser)
    if match is None:
        print('Could not update match')
        return False

    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE match SET winner='{}', sets={} WHERE player_1 = '{}' and player_2 = '{}' and season={}"\
              .format(winner.slack_id, sets, match.player_1_id, match.player_2_id, match.season))
    conn.commit()
    conn.close()
    return True

def get_current_season():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(season) FROM match")
    rows = c.fetchall()
    conn.close()
    current_season = rows[0][0]
    if current_season is None:
        return 0
    return current_season
