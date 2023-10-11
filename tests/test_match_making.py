import datetime
from unittest import TestCase

import test_league_setup
from backend import db, match_making

league_name = 'test'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_create_matches(self):
        db.add_player(league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(league_name, u'playerA4', 'Player A4', 'A')
        p1 = db.get_player_by_id(league_name, u'playerA1')
        p2 = db.get_player_by_id(league_name, u'playerA2')
        p3 = db.get_player_by_id(league_name, u'playerA3')
        p4 = db.get_player_by_id(league_name, u'playerA4')
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        matches = match_making.create_matches(week, db.get_players(league_name), skip_weeks, False)

        self.assertEqual(6, len(matches))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p4 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p3 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 17)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p2 and x['player_2'] == p3 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p4 and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p3 and x['player_2'] == p4 and x['week'] == datetime.date(2022, 1, 17)]))

    def test_create_matches_skip_weeks(self):
        db.add_player(league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(league_name, u'playerA4', 'Player A4', 'A')
        week = datetime.date(2022, 1, 3)
        skip_weeks = [datetime.date(2022, 1, 10), datetime.date(2022, 1, 24)]
        matches = match_making.create_matches(week, db.get_players(league_name), skip_weeks, False)

        self.assertEqual(6, len(matches))
        self.assertEqual(2, len([x for x in matches if x['week'] == week]))
        self.assertEqual(2, len([x for x in matches if x['week'] == datetime.date(2022, 1, 17)]))
        self.assertEqual(2, len([x for x in matches if x['week'] == datetime.date(2022, 1, 31)]))

    def test_create_matches_byes(self):
        db.add_player(league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(league_name, u'playerA3', 'Player A3', 'A')
        p1 = db.get_player_by_id(league_name, u'playerA1')
        p2 = db.get_player_by_id(league_name, u'playerA2')
        p3 = db.get_player_by_id(league_name, u'playerA3')
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        matches = match_making.create_matches(week, db.get_players(league_name), skip_weeks, True)

        self.assertEqual(6, len(matches))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] is None and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p3 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 17)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p2 and x['player_2'] == p3 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] is None and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p3 and x['player_2'] is None and x['week'] == datetime.date(2022, 1, 17)]))

    def test_create_matches_no_byes(self):
        db.add_player(league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(league_name, u'playerA4', 'Player A4', 'A')
        db.add_player(league_name, u'playerA5', 'Player A5', 'A')
        p1 = db.get_player_by_id(league_name, u'playerA1')
        p2 = db.get_player_by_id(league_name, u'playerA2')
        p3 = db.get_player_by_id(league_name, u'playerA3')
        p4 = db.get_player_by_id(league_name, u'playerA4')
        p5 = db.get_player_by_id(league_name, u'playerA5')
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        matches = match_making.create_matches(week, db.get_players(league_name), skip_weeks, False)

        self.assertEqual(10, len(matches))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p2 and x['player_2'] == p5 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p3 and x['player_2'] == p4 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p3 and x['week'] == week]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p4 and x['player_2'] == p5 and x['week'] == week]))

        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p5 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p2 and x['player_2'] == p3 and x['week'] == datetime.date(2022, 1, 10)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p4 and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 10)]))

        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p4 and x['week'] == datetime.date(2022, 1, 17)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p5 and x['player_2'] == p3 and x['week'] == datetime.date(2022, 1, 17)]))
        self.assertEqual(1, len([x for x in matches if x['player_1'] == p1 and x['player_2'] == p2 and x['week'] == datetime.date(2022, 1, 17)]))

    def test_create_matches_for_season(self):
        for group in ['A', 'B', 'C']:
            for p in range(1, 9):
                db.add_player(league_name, u'player{}{}'.format(group, p), 'Player {}{}'.format(group, p), group)

        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(league_name, week, 2, skip_weeks, False, False)

        matches = db.get_matches(league_name)
        self.assertEqual(84, len(matches))
        self.assertEqual(84, len([x for x in matches if x.sets_needed == 2]))
        self.assertEqual(28, len([x for x in matches if x.grouping == 'A']))
        self.assertEqual(28, len([x for x in matches if x.grouping == 'B']))
        self.assertEqual(28, len([x for x in matches if x.grouping == 'C']))

        self.assertEqual(1, db.get_current_season(league_name))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, week)))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 1, 10))))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 1, 17))))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 1, 24))))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 1, 31))))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 2, 7))))
        self.assertEqual(12, len(db.get_matches_for_week(league_name, datetime.date(2022, 2, 14))))

        match_making.create_matches_for_season(league_name, datetime.date(2022, 2, 21), 4, skip_weeks, False, False)
        matches = db.get_matches(league_name)
        self.assertEqual(168, len(matches))
        self.assertEqual(84, len([x for x in matches if x.sets_needed == 4]))
        self.assertEqual(84, len(db.get_matches_for_season(league_name, 2)))
        self.assertEqual(2, db.get_current_season(league_name))
