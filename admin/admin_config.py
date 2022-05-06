import sqlite3
import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "admin_config.sqlite"))

SERVER_HOST = 'SERVER_HOST'
SERVER_USER = 'SERVER_USER'
SERVER_PORT = 'SERVER_PORT'
BOT_COMMAND = 'BOT_COMMAND'
HAS_CONNECTED = 'HAS_CONNECTED'
HAS_DEPLOYED = 'HAS_DEPLOYED'
LAST_DOWNLOADED = 'LAST_DOWNLOADED'
CURRENT_LEAGUE = 'CURRENT_LEAGUE'

LEAGUE_CONFIGS = [SERVER_HOST, SERVER_USER, SERVER_PORT, BOT_COMMAND, HAS_CONNECTED, HAS_DEPLOYED]


def _get_connection():
    return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)


def initialize():
    if os.path.exists(path):
        return
    # Connecting to the database file
    conn = _get_connection()
    c = conn.cursor()

    # not sure if we'd ever need a config value that isn't text
    c.execute('CREATE TABLE config ('
              'league_name TEXT, '
              'config_name TEXT, '
              'value TEXT)')
    c.execute('CREATE TABLE universal_config ('
              'name TEXT PRIMARY KEY, '
              'value TEXT)')

    # Committing changes and closing the connection to the database file
    conn.commit()
    conn.close()


def _set_universal_config(name, value):
    conn = _get_connection()
    c = conn.cursor()

    c.execute("INSERT INTO universal_config VALUES ('{}', '{}') "
              "ON CONFLICT(name) DO UPDATE SET value='{}' where name='{}'".format(name, value, value, name))
    conn.commit()
    conn.close()


def _get_universal_config(name):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM universal_config WHERE name = '{}'".format(name))
    rows = c.fetchall()
    conn.close()
    if rows:
        return rows[0][0]
    return None


def set_config(league_name, config_name, value):
    existing = get_config(league_name, config_name)

    conn = _get_connection()
    c = conn.cursor()
    if existing is None:
        c.execute("INSERT INTO config VALUES ('{}', '{}', '{}') ".format(league_name, config_name, value))
    else:
        c.execute("UPDATE config SET value='{}' where league_name='{}' and config_name='{}'".format(value, league_name, config_name))
    conn.commit()
    conn.close()


def get_config(league_name, config_name):
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM config WHERE league_name='{}' and config_name = '{}'".format(league_name, config_name))
    rows = c.fetchall()
    conn.close()
    if rows:
        return rows[0][0]
    return None


def get_leagues():
    initialize()
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT distinct league_name FROM config")
    rows = c.fetchall()
    conn.close()
    return [x[0] for x in rows]


def get_current_league():
    initialize()
    return _get_universal_config(CURRENT_LEAGUE)


def set_current_league(league_name):
    initialize()
    _set_universal_config(CURRENT_LEAGUE, league_name)


def add_league(league_name, server_options):
    initialize()
    for config_name, value in server_options.items():
        set_config(league_name, config_name, str(value))


def get_league_configs(league_name):
    configs = {}
    for config_key in LEAGUE_CONFIGS:
        configs[config_key] = get_config(league_name, config_key)
    return configs


# useful for debugging
def print_db():
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM config")
    rows = c.fetchall()
    print(rows)

    c.execute("SELECT * FROM universal_config")
    rows = c.fetchall()
    print(rows)
    conn.close()
