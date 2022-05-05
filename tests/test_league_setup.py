import os

from backend import db, league_context

lctx = league_context.LeagueContext("test")


def teardown_test_league():
    if os.path.exists(db.path(lctx)):
        os.remove(db.path(lctx))


def create_test_league():
    db.initialize(lctx)


def add_players():
    groupsEven = ['A', 'C', 'E']
    groupsOdd = ['B', 'D', 'F']
    for group in groupsEven:
        for i in range(0, 8):
            db.add_player(lctx, u'player{}{}'.format(group, i), 'Player {}{}'.format(group, i), group)
    for group in groupsOdd:
        for i in range(0, 9):
            db.add_player(lctx, u'player{}{}'.format(group, i), 'Player {}{}'.format(group, i), group)
    print(db.get_players(lctx))


# create_test_league()
# add_players()
# teardown_test_league()
