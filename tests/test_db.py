import datetime
import sqlite3
from unittest import TestCase

import test_league_setup
from backend import db, league_context

lctx = league_context.LeagueContext('test')


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_set_config(self):
        num_commands = len(db.get_commands_to_run(lctx))
        db.set_config(lctx, 'test_config', 'test_value')
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual('test_value', db.get_config(lctx, 'test_config'))
        db.set_config(lctx, 'test_config', 'new_value')
        self.assertEqual('new_value', db.get_config(lctx, 'test_config'))

    def test_add_player(self):
        num_commands = len(db.get_commands_to_run(lctx))
        db.add_player(lctx, u'testplayer', 'Test Player', 'A')
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(1, len(db.get_players(lctx)))

        with self.assertRaises(sqlite3.IntegrityError) as exception_context:
            db.add_player(lctx, u'testplayer', 'Same ID', 'A')

    def test_set_active(self):
        db.add_player(lctx, u'testplayer', 'Test Player', 'A')
        self.assertEqual(1, db.get_players(lctx)[0].active)

        num_commands = len(db.get_commands_to_run(lctx))
        db.set_active(lctx, u'testplayer', False)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(0, db.get_players(lctx)[0].active)
        db.set_active(lctx, u'testplayer', True)
        self.assertEqual(1, db.get_players(lctx)[0].active)

    def test_get_active_players(self):
        db.add_player(lctx, u'testplayer1', 'Test Player', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        db.add_player(lctx, u'testplayer3', 'Test Player3', 'A')

        self.assertEqual(3, len(db.get_active_players(lctx)))
        db.set_active(lctx, 'testplayer1', False)
        db.set_active(lctx, 'testplayer2', False)
        self.assertEqual(1, len(db.get_active_players(lctx)))

    def test_get_player_by_name(self):
        db.add_player(lctx, u'testplayer1', 'Test Player', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        db.add_player(lctx, u'testplayer3', 'Test Player3', 'A')

        self.assertEqual(u'testplayer2', db.get_player_by_name(lctx, 'Test Player2').slack_id)
        self.assertIsNone(db.get_player_by_name(lctx, 'Not A Player'))

    def test_get_player_by_id(self):
        db.add_player(lctx, u'testplayer1', 'Test Player', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        db.add_player(lctx, u'testplayer3', 'Test Player3', 'A')

        self.assertEqual('Test Player2', db.get_player_by_id(lctx, u'testplayer2').name)
        self.assertIsNone(db.get_player_by_id(lctx, u'notaplayer'))

    def test_update_grouping(self):
        db.add_player(lctx, u'testplayer1', 'Test Player', 'A')
        num_commands = len(db.get_commands_to_run(lctx))
        db.update_grouping(lctx, u'testplayer1', 'B')
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual('B', db.get_player_by_id(lctx, u'testplayer1').grouping)

        db.update_grouping(lctx, u'testplayer1', '')
        self.assertEqual('', db.get_player_by_id(lctx, u'testplayer1').grouping)

    def test_add_match(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week = datetime.date(2020, 1, 1)

        num_commands = len(db.get_commands_to_run(lctx))
        db.add_match(lctx, p1, p2, week, 'A', 1, 3)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(1, len(db.get_matches(lctx)))
        # TODO build in protection against adding identical matches

        db.add_match(lctx, p1, None, week, 'A', 1, 3)
        db.add_match(lctx, None, p2, week, 'A', 1, 3)
        self.assertEqual(3, len(db.get_matches(lctx)))

    def test_get_current_season(self):
        self.assertEqual(0, db.get_current_season(lctx))

        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week, 'A', 3, 3)

        self.assertEqual(3, db.get_current_season(lctx))

    def test_get_matches_for_season(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week, 'A', 1, 3)
        db.add_match(lctx, p1, p2, week, 'B', 2, 3)
        db.add_match(lctx, p1, p2, week, 'C', 3, 3)

        self.assertEqual(1, len(db.get_matches_for_season(lctx, 2)))
        self.assertEqual('B', db.get_matches_for_season(lctx, 2)[0].grouping)

    def test_clear_matches_for_season(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)
        db.add_match(lctx, p1, p2, week2, 'A', 2, 3)

        num_commands = len(db.get_commands_to_run(lctx))
        db.clear_matches_for_season(lctx, 3)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(2, len(db.get_matches(lctx)))
        db.clear_matches_for_season(lctx, 1)
        self.assertEqual(1, len(db.get_matches(lctx)))

    def test_get_matches_for_week(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)
        db.add_match(lctx, p1, p2, week2, 'A', 2, 3)

        self.assertEqual(1, len(db.get_matches_for_week(lctx, week1)))
        self.assertEqual(0, len(db.get_matches_for_week(lctx, datetime.date(1999, 1, 1))))

    def test_get_match_by_players(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        db.add_player(lctx, u'testplayer3', 'Test Player3', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        p3 = db.get_player_by_id(lctx, u'testplayer3')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)
        db.add_match(lctx, p1, p2, week2, 'A', 2, 3)

        self.assertIsNone(db.get_match_by_players(lctx, p1, p1))
        self.assertIsNone(db.get_match_by_players(lctx, p1, p3))
        self.assertEqual(week2, db.get_match_by_players(lctx, p1, p2).week)
        self.assertEqual(week2, db.get_match_by_players(lctx, p2, p1).week)

    def test__update_match(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)

        self.assertEqual(0, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertIsNone(db.get_match_by_players(lctx, p1, p2).winner_id)
        self.assertIsNone(db.get_match_by_players(lctx, p1, p2).date_played)

        # sets out of range
        num_commands = len(db.get_commands_to_run(lctx))
        db._update_match(lctx, p1, p2, 2)
        self.assertEqual(0, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertIsNone(db.get_match_by_players(lctx, p1, p2).winner_id)
        db._update_match(lctx, p1, p2, 6)
        self.assertEqual(0, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertIsNone(db.get_match_by_players(lctx, p1, p2).winner_id)
        self.assertEqual(num_commands, len(db.get_commands_to_run(lctx)))

        db._update_match(lctx, p1, p2, 5)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(5, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertEqual(p1.slack_id, db.get_match_by_players(lctx, p1, p2).winner_id)
        self.assertEqual(datetime.date.today(), db.get_match_by_players(lctx, p1, p2).date_played)

        db._update_match(lctx, p2, p1, 3)
        self.assertEqual(3, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertEqual(p2.slack_id, db.get_match_by_players(lctx, p1, p2).winner_id)

    def test_update_match(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)

        num_commands = len(db.get_commands_to_run(lctx))
        db.update_match(lctx, 'Test Player1', 'Test Player2', 3)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(3, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertEqual(p1.slack_id, db.get_match_by_players(lctx, p1, p2).winner_id)

    def test_update_match_by_id(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)

        num_commands = len(db.get_commands_to_run(lctx))
        db.update_match_by_id(lctx, u'testplayer1', u'testplayer2', 3)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)
        self.assertEqual(3, db.get_match_by_players(lctx, p1, p2).sets)
        self.assertEqual(p1.slack_id, db.get_match_by_players(lctx, p1, p2).winner_id)

    def test_admin_update_match(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)

        match = db.get_match_by_players(lctx, p1, p2)
        match.player_1_id = 'arbitrary1'
        match.player_2_id = 'arbitrary2'
        match.winner_id = None
        match.week = datetime.date(2021, 1, 1)
        match.grouping = 'B'
        match.sets = 9
        match.sets_needed = 1

        num_commands = len(db.get_commands_to_run(lctx))
        db.admin_update_match(lctx, match)
        self.assertEqual(1, len(db.get_commands_to_run(lctx)) - num_commands)
        updatedMatch = db.get_matches(lctx)[0]
        self.assertEqual('arbitrary1', updatedMatch.player_1_id)
        self.assertEqual('arbitrary2', updatedMatch.player_2_id)
        self.assertIsNone(updatedMatch.winner_id)
        self.assertEqual(datetime.date(2021, 1, 1), updatedMatch.week)
        self.assertEqual('B', updatedMatch.grouping)
        self.assertEqual(9, updatedMatch.sets)
        self.assertEqual(1, updatedMatch.sets_needed)

    def test_get_all_seasons(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(lctx, p1, p2, week1, 'A', 1, 3)
        db.add_match(lctx, p1, p2, week1, 'A', 2, 3)
        db.add_match(lctx, p1, p2, week1, 'A', 3, 3)
        all_seasons = db.get_all_seasons(lctx)
        all_seasons.sort()
        self.assertEqual([1, 2, 3], all_seasons)

    def test_update_player_order_idx(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        self.assertEqual(0, p1.order_idx)

        num_commands = len(db.get_commands_to_run(lctx))
        db.update_player_order_idx(lctx, p1.slack_id, 5)
        self.assertEqual(5, db.get_player_by_id(lctx, u'testplayer1').order_idx)
        self.assertEqual(1, len(db.get_commands_to_run(lctx))-num_commands)

    def test_updating_grouping_and_orders(self):
        db.add_player(lctx, u'testplayer1', 'Test Player1', 'A')
        db.add_player(lctx, u'testplayer2', 'Test Player2', 'B')
        db.add_player(lctx, u'testplayer3', 'Test Player3', 'C')
        db.add_player(lctx, u'testplayer4', 'Test Player4', 'D')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        p3 = db.get_player_by_id(lctx, u'testplayer3')
        p4 = db.get_player_by_id(lctx, u'testplayer4')
        db.set_active(lctx, u'testplayer1', False)
        self.assertEqual(0, p1.order_idx)
        self.assertEqual(0, p2.order_idx)
        self.assertEqual(0, p3.order_idx)
        self.assertEqual(0, p4.order_idx)
        self.assertEqual('A', p1.grouping)
        self.assertEqual('B', p2.grouping)
        self.assertEqual('C', p3.grouping)
        self.assertEqual('D', p4.grouping)

        num_commands = len(db.get_commands_to_run(lctx))
        db.updating_grouping_and_orders(lctx, [x.slack_id for x in [p1, p2, p3, p4]], 'E')
        p1 = db.get_player_by_id(lctx, u'testplayer1')
        p2 = db.get_player_by_id(lctx, u'testplayer2')
        p3 = db.get_player_by_id(lctx, u'testplayer3')
        p4 = db.get_player_by_id(lctx, u'testplayer4')
        self.assertEqual(1, p1.active)
        self.assertEqual(0, p1.order_idx)
        self.assertEqual(1, p2.order_idx)
        self.assertEqual(2, p3.order_idx)
        self.assertEqual(3, p4.order_idx)
        self.assertEqual('E', p1.grouping)
        self.assertEqual('E', p2.grouping)
        self.assertEqual('E', p3.grouping)
        self.assertEqual('E', p4.grouping)
        self.assertEqual(4, len(db.get_commands_to_run(lctx))-num_commands)
