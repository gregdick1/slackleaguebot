import sqlite3
import os
from backend import db, league_context
from admin import admin_context, db_management
# Script for importing an older league into the new format

# Assumptions for this to work
# 1. Your new db needs to be fresh. No matches or players. This will import everything as is which would
#    collide with anything in the new db.
# 2. You need to have connected the new league to the server already. This will push up the db when it's done.

old_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "hudl_pong_league.sqlite"))
new_league_name = 'test2'

old_db_conn = sqlite3.connect(old_db_path, detect_types=sqlite3.PARSE_DECLTYPES)
c = old_db_conn.cursor()
c.execute('SELECT * FROM player')
old_players = c.fetchall()

c.execute('SELECT * FROM match')
old_matches = c.fetchall()
old_db_conn.close()

lctx = league_context.LeagueContext(new_league_name)
new_db_conn = db.get_connection(lctx)
c = new_db_conn.cursor()

c.execute("DELETE FROM player")
c.execute("DELETE FROM match")
new_db_conn.commit()

for row in old_players:
    # Players haven't changed, we can import as-is
    command = "INSERT INTO player VALUES ('{}', '{}', '{}', {})".format(row[0], row[1].replace("'","''"), row[2], row[3])
    print(command)
    c.execute(command)


sets_per_season = {}
for old_match in old_matches:
    # We've added sets_needed and need to figure out what that is for each season
    season = old_match[5]
    sets = old_match[6]
    if season not in sets_per_season:
        sets_per_season[season] = {'min': 100, 'max': 0}
    if sets > 0:
        if sets < sets_per_season[season]['min']:
            sets_per_season[season]['min'] = sets
        if sets > sets_per_season[season]['max']:
            sets_per_season[season]['max'] = sets
sets_needed_per_season = {}
for season in sets_per_season:
    smin = sets_per_season[season]['min']
    smax = sets_per_season[season]['max']
    sets_needed_per_season[season] = smin
    if smin != (smax+1)/2:
        print("Can't confirm sets needed for season " + season)


for old_match in old_matches:
    player_1_id = old_match[0]
    player_2_id = old_match[1]
    winner_id = old_match[2]
    week = old_match[3]
    grouping = old_match[4]
    season = old_match[5]
    sets = old_match[6]

    command = "INSERT INTO match VALUES (" + \
              ("'{}', ".format(player_1_id) if player_1_id is not None else "null, ") + \
              ("'{}', ".format(player_2_id) if player_2_id is not None else "null, ") + \
              ("'{}', ".format(winner_id) if winner_id is not None else "null, ") + \
              "'{}', ".format(week) + \
              "'{}', ".format(grouping) + \
              "{}, ".format(season) + \
              "{}, ".format(sets) + \
              "{})".format(sets_needed_per_season[season])
    print(command)
    c.execute(command)

new_db_conn.commit()
new_db_conn.close()

actx = admin_context.Context.load_from_db(new_league_name)
db_management._upload_db(actx)
