import os

from backend import db

league_name = "test"


def teardown_test_league():
    if os.path.exists(db.path(league_name)):
        os.remove(db.path(league_name))


def create_test_league():
    db.initialize(league_name)


def add_players():
    groupsEven = ['A', 'C', 'E']
    groupsOdd = ['B', 'D', 'F']
    for group in groupsEven:
        for i in range(0, 8):
            db.add_player(league_name, u'player{}{}'.format(group, i), 'Player {}{}'.format(group, i), group)
    for group in groupsOdd:
        for i in range(0, 9):
            db.add_player(league_name, u'player{}{}'.format(group, i), 'Player {}{}'.format(group, i), group)
    print(db.get_players(league_name))


# create_test_league()
# add_players()
# teardown_test_league()
