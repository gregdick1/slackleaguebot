from backend import db, utility, configs


def run_updates(league_name):
    current_version = db.get_config(league_name, configs.LEAGUE_VERSION)
    if current_version == '0':
        _update_from_0_to_1(league_name)
        current_version = '1'
    if current_version == '1':
        _update_from_1_to_2(league_name)
        current_version = '2'


# Adds the ordering index to players
# Adds date played on match
# Adds message sent flag on match
def _update_from_0_to_1(league_name):
    current_version = db.get_config(league_name, configs.LEAGUE_VERSION)
    if not current_version or current_version != '0':
        return False

    conn = db.get_connection(league_name)
    c = conn.cursor()

    c.execute("ALTER TABLE player ADD order_idx INT DEFAULT 0")
    c.execute("ALTER TABLE match ADD date_played DATE")
    c.execute("ALTER TABLE match ADD message_sent INT DEFAULT 1")
    c.execute("UPDATE match SET date_played = week WHERE winner is not null")
    conn.commit()
    conn.close()

    last_season_matches = db.get_matches_for_season(league_name, db.get_current_season(league_name))
    groupings = list(set([x.grouping for x in last_season_matches]))
    groupings.sort()
    for grouping in groupings:
        group_matches = [m for m in last_season_matches if m.grouping == grouping]
        players = utility.gather_scores(group_matches)
        for idx, p in enumerate(players):
            db.update_player_order_idx(league_name, p['player_id'], idx)

    db.set_config(league_name, configs.LEAGUE_VERSION, '1')


# Adds the commands table
def _update_from_1_to_2(league_name):
    current_version = db.get_config(league_name, configs.LEAGUE_VERSION)
    if not current_version or current_version != '1':
        return False

    conn = db.get_connection(league_name)
    c = conn.cursor()
    c.execute('CREATE TABLE commands_to_run ('
              'command_id INTEGER PRIMARY KEY AUTOINCREMENT, '
              'command_text text NOT NULL)')
    conn.commit()
    conn.close()

    db.set_config(league_name, configs.LEAGUE_VERSION, '2')
