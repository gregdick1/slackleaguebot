import sqlite3
import datetime
import os
import subprocess

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../league_competition_config.sqlite"))

def get_connection():
    return sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

def create_table():
    # Connecting to the database file
    conn = get_connection()
    c = conn.cursor()

    #not sure if we'd ever need a config value that isn't text
    c.execute('CREATE TABLE config ('
              'name TEXT PRIMARY KEY, '
              'value TEXT)')

    # Committing changes and closing the connection to the database file
    conn.commit()
    conn.close()

def set_config(name, value):
    conn = get_connection()
    c = conn.cursor()

    c.execute("INSERT INTO config VALUES ('{}', '{}') "
               "ON CONFLICT(name) DO UPDATE SET value='{}' where name='{}'".format(name, value, value, name))
    conn.commit()
    conn.close()

# create_table()
set_config('test', 'test_value2')