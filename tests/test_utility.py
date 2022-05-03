from unittest import TestCase

from backend import db, league_context, match_making, utility
import test_league_setup
import datetime

lctx = league_context.LeagueContext('test')


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_gather_scores(self):
        db.add_player(lctx, u'playerA1', 'Player A1', 'A')
        db.add_player(lctx, u'playerA2', 'Player A2', 'A')
        db.add_player(lctx, u'playerA3', 'Player A3', 'A')
        db.add_player(lctx, u'playerA4', 'Player A4', 'A')
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx, week, 4, skip_weeks, False)

        db.update_match(lctx, 'Player A1', 'Player A2', 4)
        db.update_match(lctx, 'Player A1', 'Player A3', 5)
        db.update_match(lctx, 'Player A1', 'Player A4', 6)
        db.update_match(lctx, 'Player A3', 'Player A2', 7)
        db.update_match(lctx, 'Player A4', 'Player A2', 6)
        db.update_match(lctx, 'Player A4', 'Player A3', 5)

        matches = db.get_matches(lctx)
        results = utility.gather_scores(matches)
        self.assertEqual(results[0], {'player_id': 'playerA1', 'm_w': 3, 'm_l': 0, 's_w': 12, 's_l': 3})
        self.assertEqual(results[1], {'player_id': 'playerA4', 'm_w': 2, 'm_l': 1, 's_w': 10, 's_l': 7})
        self.assertEqual(results[2], {'player_id': 'playerA3', 'm_w': 1, 'm_l': 2, 's_w': 6, 's_l': 11})
        self.assertEqual(results[3], {'player_id': 'playerA2', 'm_w': 0, 'm_l': 3, 's_w': 5, 's_l': 12})

    # TODO test the printout function