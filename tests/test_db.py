import datetime
import sqlite3
from unittest import TestCase

import test_league_setup
from backend import db

league_name = 'unittest'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_set_config(self):
        num_commands = len(db.get_commands_to_run(league_name))
        db.set_config(league_name, 'test_config', 'test_value')
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual('test_value', db.get_config(league_name, 'test_config'))
        db.set_config(league_name, 'test_config', 'new_value')
        self.assertEqual('new_value', db.get_config(league_name, 'test_config'))

    def test_add_player(self):
        num_commands = len(db.get_commands_to_run(league_name))
        db.add_player(league_name, u'testplayer', 'Test Player', 'A')
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(1, len(db.get_players(league_name)))

        with self.assertRaises(sqlite3.IntegrityError) as exception_context:
            db.add_player(league_name, u'testplayer', 'Same ID', 'A')

    def test_add_player_unique_constraint(self):
        num_commands = len(db.get_commands_to_run(league_name))
        db.add_player(league_name, u'testplayer', 'Test Player', 'A')
        try:
            db.add_player(league_name, u'testplayer', 'Test Player Again', 'A')
        except:
            pass
        db.add_player(league_name, u'testplayer2', 'Test Player 2', 'A')
        self.assertEqual(2, len(db.get_commands_to_run(league_name)) - num_commands)

    def test_set_active(self):
        db.add_player(league_name, u'testplayer', 'Test Player', 'A')
        self.assertEqual(1, db.get_players(league_name)[0].active)

        num_commands = len(db.get_commands_to_run(league_name))
        db.set_active(league_name, u'testplayer', False)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(0, db.get_players(league_name)[0].active)
        db.set_active(league_name, u'testplayer', True)
        self.assertEqual(1, db.get_players(league_name)[0].active)

    def test_get_active_players(self):
        db.add_player(league_name, u'testplayer1', 'Test Player', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual(3, len(db.get_active_players(league_name)))
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))

        db.set_active(league_name, 'testplayer1', False)
        db.set_active(league_name, 'testplayer2', False)
        self.assertEqual(1, len(db.get_active_players(league_name)))

    def test_get_player_by_name(self):
        db.add_player(league_name, u'testplayer1', 'Test Player', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual(u'testplayer2', db.get_player_by_name(league_name, 'Test Player2').slack_id)
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))
        self.assertIsNone(db.get_player_by_name(league_name, 'Not A Player'))

    def test_get_player_by_id(self):
        db.add_player(league_name, u'testplayer1', 'Test Player', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual('Test Player2', db.get_player_by_id(league_name, u'testplayer2').name)
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))
        self.assertIsNone(db.get_player_by_id(league_name, u'notaplayer'))

    def test_update_grouping(self):
        db.add_player(league_name, u'testplayer1', 'Test Player', 'A')
        num_commands = len(db.get_commands_to_run(league_name))
        db.update_grouping(league_name, u'testplayer1', 'B')
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual('B', db.get_player_by_id(league_name, u'testplayer1').grouping)

        db.update_grouping(league_name, u'testplayer1', '')
        self.assertEqual('', db.get_player_by_id(league_name, u'testplayer1').grouping)

    def test_add_match(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week = datetime.date(2020, 1, 1)

        num_commands = len(db.get_commands_to_run(league_name))
        db.add_match(league_name, p1, p2, week, 'A', 1, 0, 3)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(1, len(db.get_matches(league_name)))
        # TODO build in protection against adding identical matches

        db.add_match(league_name, p1, None, week, 'A', 1, 0, 3)
        db.add_match(league_name, None, p2, week, 'A', 1, 0, 3)
        self.assertEqual(3, len(db.get_matches(league_name)))

    def test_get_current_season(self):
        self.assertEqual(0, db.get_current_season(league_name))

        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week, 'A', 3, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual(3, db.get_current_season(league_name))
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))

    def test_get_matches_for_season(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p2, week, 'B', 2, 0, 3)
        db.add_match(league_name, p1, p2, week, 'C', 3, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual(1, len(db.get_matches_for_season(league_name, 2)))
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))
        self.assertEqual('B', db.get_matches_for_season(league_name, 2)[0].grouping)

    def test_clear_matches_for_season(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p2, week2, 'A', 2, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        db.clear_matches_for_season(league_name, 3)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(2, len(db.get_matches(league_name)))
        db.clear_matches_for_season(league_name, 1)
        self.assertEqual(1, len(db.get_matches(league_name)))

    def test_get_matches_for_week(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p2, week2, 'A', 2, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertEqual(1, len(db.get_matches_for_week(league_name, week1)))
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))
        self.assertEqual(0, len(db.get_matches_for_week(league_name, datetime.date(1999, 1, 1))))

    def test_get_match_by_players(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        week1 = datetime.date(2020, 1, 1)
        week2 = datetime.date(2021, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p2, week2, 'A', 2, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        self.assertIsNone(db.get_match_by_players(league_name, p1, p1))
        self.assertIsNone(db.get_match_by_players(league_name, p1, p3))
        self.assertEqual(week2, db.get_match_by_players(league_name, p1, p2).week)
        self.assertEqual(week2, db.get_match_by_players(league_name, p2, p1).week)
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))

    def test__update_match(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)

        self.assertEqual(0, db.get_match_by_players(league_name, p1, p2).sets)
        self.assertIsNone(db.get_match_by_players(league_name, p1, p2).winner_id)
        self.assertIsNone(db.get_match_by_players(league_name, p1, p2).date_played)

        # sets out of range
        num_commands = len(db.get_commands_to_run(league_name))

        db._update_match(league_name, p1, p2, 2, 0, 0)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(0, m.sets)
        self.assertEqual(0, m.player_1_score)
        self.assertEqual(0, m.player_2_score)
        self.assertEqual(0, m.tie_score)
        self.assertIsNone(m.winner_id)

        db._update_match(league_name, p1, p2, 3, 3, 0)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(0, m.sets)
        self.assertEqual(0, m.player_1_score)
        self.assertEqual(0, m.player_2_score)
        self.assertEqual(0, m.tie_score)
        self.assertIsNone(m.winner_id)

        db._update_match(league_name, p1, p2, 6, 0, 0)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(0, m.sets)
        self.assertEqual(0, m.player_1_score)
        self.assertEqual(0, m.player_2_score)
        self.assertEqual(0, m.tie_score)
        self.assertIsNone(m.winner_id)

        db._update_match(league_name, p1, p2, 3, 2, 0)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(5, m.sets)
        self.assertEqual(3, m.player_1_score)
        self.assertEqual(2, m.player_2_score)
        self.assertEqual(0, m.tie_score)
        self.assertEqual(p1.slack_id, m.winner_id)
        self.assertEqual(datetime.date.today(), m.date_played)

        db._update_match(league_name, p2, p1, 3, 0, 0)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(3, m.sets)
        self.assertEqual(3, m.player_2_score)
        self.assertEqual(0, m.player_1_score)
        self.assertEqual(0, m.tie_score)
        self.assertEqual(p2.slack_id, m.winner_id)

        db._update_match(league_name, p2, p1, 2, 0, 1)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(3, m.sets)
        self.assertEqual(2, m.player_2_score)
        self.assertEqual(0, m.player_1_score)
        self.assertEqual(1, m.tie_score)
        self.assertEqual(p2.slack_id, m.winner_id)

        db._update_match(league_name, p2, p1, 1, 1, 1)
        m = db.get_match_by_players(league_name, p1, p2)
        self.assertEqual(3, m.sets)
        self.assertEqual(1, m.player_2_score)
        self.assertEqual(1, m.player_1_score)
        self.assertEqual(1, m.tie_score)
        self.assertEqual(p2.slack_id, m.winner_id)

    def test_update_match(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        db.update_match(league_name, 'Test Player1', 'Test Player2', 3, 0, 0)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(3, db.get_match_by_players(league_name, p1, p2).sets)
        self.assertEqual(p1.slack_id, db.get_match_by_players(league_name, p1, p2).winner_id)

    def test_update_match_by_id(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)

        num_commands = len(db.get_commands_to_run(league_name))
        db.update_match_by_id(league_name, u'testplayer1', u'testplayer2', 3, 0, 0)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)
        self.assertEqual(3, db.get_match_by_players(league_name, p1, p2).sets)
        self.assertEqual(p1.slack_id, db.get_match_by_players(league_name, p1, p2).winner_id)

    def test_admin_update_match_score(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)

        match = db.get_match_by_players(league_name, p1, p2)

        num_commands = len(db.get_commands_to_run(league_name))
        db.admin_update_match_score(league_name, match.id, u'testplayer1', 3)
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        updated_match = db.get_matches(league_name)[0]
        self.assertEqual(u'testplayer1', updated_match.winner_id)
        self.assertEqual(3, updated_match.sets)

        db.admin_update_match_score(league_name, match.id, u'testplayer2', 5)
        updated_match = db.get_matches(league_name)[0]
        self.assertEqual(u'testplayer2', updated_match.winner_id)
        self.assertEqual(5, updated_match.sets)

    def test_update_match_players(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')
        db.add_player(league_name, u'testplayer4', 'Test Player4', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)

        match = db.get_match_by_players(league_name, p1, p2)

        num_commands = len(db.get_commands_to_run(league_name))
        db.update_match_players(league_name, match.id, u'testplayer3', u'testplayer4')
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        updated_match = db.get_matches(league_name)[0]
        self.assertEqual(u'testplayer3', updated_match.player_1_id)
        self.assertEqual(u'testplayer4', updated_match.player_2_id)

    def test_get_all_seasons(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        week1 = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week1, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p2, week1, 'A', 2, 0, 3)
        db.add_match(league_name, p1, p2, week1, 'A', 3, 0, 3)
        num_commands = len(db.get_commands_to_run(league_name))
        all_seasons = db.get_all_seasons(league_name)
        all_seasons.sort()
        self.assertEqual([1, 2, 3], all_seasons)
        self.assertEqual(num_commands, len(db.get_commands_to_run(league_name)))

    def test_update_player_order_idx(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        self.assertEqual(0, p1.order_idx)

        num_commands = len(db.get_commands_to_run(league_name))
        db.update_player_order_idx(league_name, p1.slack_id, 5)
        self.assertEqual(5, db.get_player_by_id(league_name, u'testplayer1').order_idx)
        self.assertEqual(1, len(db.get_commands_to_run(league_name))-num_commands)

    def test_updating_grouping_and_orders(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'B')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'C')
        db.add_player(league_name, u'testplayer4', 'Test Player4', 'D')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        p4 = db.get_player_by_id(league_name, u'testplayer4')
        db.set_active(league_name, u'testplayer1', False)
        self.assertEqual(0, p1.order_idx)
        self.assertEqual(0, p2.order_idx)
        self.assertEqual(0, p3.order_idx)
        self.assertEqual(0, p4.order_idx)
        self.assertEqual('A', p1.grouping)
        self.assertEqual('B', p2.grouping)
        self.assertEqual('C', p3.grouping)
        self.assertEqual('D', p4.grouping)

        num_commands = len(db.get_commands_to_run(league_name))
        db.updating_grouping_and_orders(league_name, [x.slack_id for x in [p1, p2, p3, p4]], 'E')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        p4 = db.get_player_by_id(league_name, u'testplayer4')
        self.assertEqual(1, p1.active)
        self.assertEqual(0, p1.order_idx)
        self.assertEqual(1, p2.order_idx)
        self.assertEqual(2, p3.order_idx)
        self.assertEqual(3, p4.order_idx)
        self.assertEqual('E', p1.grouping)
        self.assertEqual('E', p2.grouping)
        self.assertEqual('E', p3.grouping)
        self.assertEqual('E', p4.grouping)
        self.assertEqual(4, len(db.get_commands_to_run(league_name))-num_commands)

    def test_add_reminder_day(self):
        num_commands = len(db.get_commands_to_run(league_name))
        date = datetime.date(2022, 1, 1)
        db.add_reminder_day(league_name, 3, date)
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        self.assertEqual([{'date': date, 'season': 3, 'sent': 0}], db.get_reminder_days_since(league_name, 3, date))

        self.assertEqual(0, len(db.get_reminder_days_since(league_name, 3, date + datetime.timedelta(days=1))))

    def test_remove_reminder_day(self):
        date = datetime.date(2022, 1, 1)
        db.add_reminder_day(league_name, 3, date)
        db.add_reminder_day(league_name, 3, date + datetime.timedelta(weeks=1))
        db.add_reminder_day(league_name, 3, date + datetime.timedelta(weeks=2))

        num_commands = len(db.get_commands_to_run(league_name))
        db.remove_reminder_day(league_name, 3, date+datetime.timedelta(weeks=1))
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        self.assertEqual([{'date': date, 'season': 3, 'sent': 0}, {'date': date + datetime.timedelta(weeks=2), 'season': 3, 'sent': 0}],
                         db.get_reminder_days_since(league_name, 3, datetime.date(1970, 1, 1)))

    def test_mark_reminder_day_sent(self):
        date = datetime.date(2022, 1, 1)
        db.add_reminder_day(league_name, 3, date)
        db.add_reminder_day(league_name, 3, date + datetime.timedelta(weeks=1))
        db.add_reminder_day(league_name, 3, date + datetime.timedelta(weeks=2))

        num_commands = len(db.get_commands_to_run(league_name))
        db.mark_reminder_day_sent(league_name, 3, date + datetime.timedelta(weeks=1))
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        self.assertEqual([{'date': date, 'season': 3, 'sent': 0}, {'date': date + datetime.timedelta(weeks=1), 'season': 3, 'sent': 1}, {'date': date + datetime.timedelta(weeks=2), 'season': 3, 'sent': 0}],
                         db.get_reminder_days_since(league_name, 3, datetime.date(1970, 1, 1)))

    def test_mark_match_message_sent(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        week = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p3, week + datetime.timedelta(weeks=1), 'A', 1, 0, 3)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(0, match.message_sent)
        num_commands = len(db.get_commands_to_run(league_name))
        db.mark_match_message_sent(league_name, match.id)
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)

        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(1, match.message_sent)
        unaffected_match = db.get_matches_for_week(league_name, week + datetime.timedelta(weeks=1))[0]
        self.assertEqual(0, unaffected_match.message_sent)

        db.mark_match_message_sent(league_name, match.id, sent=0)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(0, match.message_sent)

    def test_set_match_forfeit(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        week = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p3, week + datetime.timedelta(weeks=1), 'A', 1, 0, 3)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(0, match.forfeit)
        num_commands = len(db.get_commands_to_run(league_name))
        db.set_match_forfeit(league_name, match.id)
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)

        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(1, match.forfeit)
        unaffected_match = db.get_matches_for_week(league_name, week + datetime.timedelta(weeks=1))[0]
        self.assertEqual(0, unaffected_match.forfeit)

        db.set_match_forfeit(league_name, match.id, forfeit=0)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(0, match.forfeit)

    def test_clear_score_for_match(self):
        db.add_player(league_name, u'testplayer1', 'Test Player1', 'A')
        db.add_player(league_name, u'testplayer2', 'Test Player2', 'A')
        db.add_player(league_name, u'testplayer3', 'Test Player3', 'A')
        p1 = db.get_player_by_id(league_name, u'testplayer1')
        p2 = db.get_player_by_id(league_name, u'testplayer2')
        p3 = db.get_player_by_id(league_name, u'testplayer3')
        week = datetime.date(2020, 1, 1)
        db.add_match(league_name, p1, p2, week, 'A', 1, 0, 3)
        db.add_match(league_name, p1, p3, week+datetime.timedelta(weeks=1), 'A', 1, 0, 3)

        db.update_match_by_id(league_name, u'testplayer1', u'testplayer2', 3, 1, 1)
        db.update_match_by_id(league_name, u'testplayer3', u'testplayer1', 1, 3, 0)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertEqual(u'testplayer1', match.winner_id)
        self.assertEqual(5, match.sets)
        self.assertEqual(3, match.player_1_score)
        self.assertEqual(1, match.player_2_score)
        self.assertEqual(1, match.tie_score)
        self.assertIsNotNone(match.date_played)

        num_commands = len(db.get_commands_to_run(league_name))
        db.clear_score_for_match(league_name, match.id)
        self.assertEqual(1, len(db.get_commands_to_run(league_name)) - num_commands)
        match = db.get_matches_for_week(league_name, week)[0]
        self.assertIsNone(match.winner_id)
        self.assertEqual(0, match.sets)
        self.assertEqual(0, match.player_1_score)
        self.assertEqual(0, match.player_2_score)
        self.assertEqual(0, match.tie_score)
        self.assertIsNone(match.date_played)

        unaffected = db.get_matches_for_week(league_name, week+datetime.timedelta(weeks=1))[0]
        self.assertEqual(u'testplayer3', unaffected.winner_id)
        self.assertEqual(4, unaffected.sets)
        self.assertIsNotNone(unaffected.date_played)
