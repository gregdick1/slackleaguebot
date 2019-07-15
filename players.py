# Fill player_map with player names and assignments when ready to run
player_map = {}

import slack
import db
import match_making

def ensure_players_in_db():
    existing = db.get_players()
    local_player_map = player_map.copy()
    for player in existing:
        if player.name in local_player_map:
            del local_player_map[player.name]

    if len(local_player_map) == 0:
        return

    # Get users list
    response = slack.slack_client.users.list()
    users = response.body['members']
    user_map = {}
    for user in users:
        for name, grouping in local_player_map.iteritems():

            if user['profile']['real_name'].startswith(name) and not user['deleted']:
                user_map[name] = user['id']
                db.add_player(user['id'], name, grouping)

    if len(user_map) != len(local_player_map):
        for key, value in user_map.iteritems():
            del local_player_map[key]
        print 'Could not find slack ids for the following ', local_player_map

def update_groupings():
    ensure_players_in_db()
    existing = db.get_players()

    for name, grouping in player_map.iteritems():
        for e in existing:
            if e.name == name:
                db.update_grouping(e.slack_id, grouping)
                if grouping == '':
                    db.set_active(e.slack_id, False)
                else:
                    db.set_active(e.slack_id, True)

def print_new_groups():
    season = db.get_current_season()
    all_matches = db.get_matches_for_season(season)
    all_players = db.get_players()
    groups = sorted(list(set([m.grouping for m in all_matches])))
    last_group_letter = ''
    last_group = []
    last_relegated = []
    last_relegated_2 = []
    for group in groups:
        group_matches = [m for m in all_matches if m.grouping == group]
        players = match_making.gather_scores(group_matches)
        promoted = players[:2]

        player_names = []

        if len(last_group):
            for player in last_group + promoted + last_relegated_2:
                name = [p.name for p in all_players if p.slack_id == player['player_id']][0]
                print "u'"+name+"': '"+last_group_letter+"',"

        last_relegated_2 = last_relegated[:]
        last_relegated = players[-2:]
        last_group = players[2:len(players)-2]
        last_group_letter = group
    player_names = []
    for player in last_group + last_relegated_2:
        name = [p.name for p in all_players if p.slack_id == player['player_id']][0]
        print "u'" + name + "': '" + last_group_letter + "',"

# print_new_groups()