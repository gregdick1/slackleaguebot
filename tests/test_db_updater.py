import os
import sqlite3
from unittest import TestCase

import test_league_setup
from backend import db, configs

league_name = 'unittest'

V6_DDL = [
    'CREATE TABLE player (slack_id TEXT PRIMARY KEY, name TEXT, grouping TEXT, active INT, order_idx INT DEFAULT 0)',
    'CREATE TABLE match (player_1 TEXT, player_2 TEXT, winner TEXT, week DATE, grouping TEXT, season INT, sets INT, '
    'sets_needed INT, date_played DATE, message_sent INT DEFAULT 0, forfeit INT DEFAULT 0, player_1_score INT, '
    'player_2_score INT, tie_score INT, play_all_sets DEFAULT 0, FOREIGN KEY (player_1) REFERENCES player, '
    'FOREIGN KEY (player_2) REFERENCES player, FOREIGN KEY (winner) REFERENCES player)',
    'CREATE TABLE config (name TEXT PRIMARY KEY, value TEXT)',
    'CREATE TABLE commands_to_run (command_id INTEGER PRIMARY KEY AUTOINCREMENT, command_text text NOT NULL)',
    'CREATE TABLE reminder_days (date DATE, sent INT, season INT DEFAULT 0)',
]


def write_v6_db():
    # Must run before any db.* call: db.get_config auto-initializes a fresh v7 DB when the file is missing.
    conn = sqlite3.connect(db.path(league_name))
    c = conn.cursor()
    for ddl in V6_DDL:
        c.execute(ddl)
    c.execute("INSERT INTO config VALUES ('LEAGUE_VERSION', '6')")
    c.execute("INSERT INTO player VALUES ('p1', 'P One', 'A', 1, 0)")
    c.execute("INSERT INTO player VALUES ('p2', 'P Two', 'A', 1, 1)")
    c.execute("INSERT INTO match VALUES ('p1', 'p2', 'p1', '2022-01-03', 'A', 1, 4, 3, '2022-01-04', 1, 0, 3, 1, 0, 0)")
    conn.commit()
    conn.close()


def dump(table):
    conn = sqlite3.connect(db.path(league_name))
    rows = conn.execute('SELECT * FROM {}'.format(table)).fetchall()
    conn.close()
    return rows


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_migrates_v6_to_v7(self):
        write_v6_db()
        matches_before, players_before = dump('match'), dump('player')
        from admin import db_updater
        db_updater.run_updates(league_name)
        self.assertEqual('7', db.get_config(league_name, configs.LEAGUE_VERSION))
        self.assertEqual('SINGLES', db.get_config(league_name, configs.LEAGUE_FORMAT))
        self.assertEqual([], dump('team'))
        self.assertEqual(matches_before, dump('match'))
        self.assertEqual(players_before, dump('player'))

    def test_migration_keeps_existing_format(self):
        write_v6_db()
        conn = sqlite3.connect(db.path(league_name))
        conn.execute("INSERT INTO config VALUES ('LEAGUE_FORMAT', 'DOUBLES')")
        conn.commit()
        conn.close()
        from admin import db_updater
        db_updater.run_updates(league_name)
        self.assertEqual('DOUBLES', db.get_config(league_name, configs.LEAGUE_FORMAT))

    def test_migration_idempotent_when_team_table_exists(self):
        # A crash after CREATE TABLE but before version bump leaves the table.
        # The next run of run_updates must not raise "table team already exists".
        write_v6_db()
        import sqlite3
        conn = sqlite3.connect(db.path(league_name))
        conn.execute(db.TEAM_TABLE_DDL)
        conn.commit()
        conn.close()
        from admin import db_updater
        db_updater.run_updates(league_name)  # must not raise
        self.assertEqual('7', db.get_config(league_name, configs.LEAGUE_VERSION))

    def test_fresh_initialize_is_v7(self):
        test_league_setup.create_test_league()
        self.assertEqual(str(db.LATEST_VERSION), db.get_config(league_name, configs.LEAGUE_VERSION))
        self.assertEqual(7, db.LATEST_VERSION)
        self.assertEqual('SINGLES', db.get_config(league_name, configs.LEAGUE_FORMAT))
        self.assertEqual([], dump('team'))
