from unittest import TestCase
from unittest.mock import patch
import datetime, collections

from backend import slack_util, db, match_making
from backend.commands import leaderboard
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext
from tests import test_league_setup

lctx = None


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'unittest'
        global lctx
        lctx = LeagueContext.load_from_db(league_name)

        for g in ['A', 'B', 'C']:
            for i in range(1, 12):  # Odd number to get some byes
                db.add_player(lctx.league_name, 'player{}{}'.format(g, i), 'Player {}{}'.format(g, i), g)
        for i in range(1, 13):
            db.add_player(lctx.league_name, 'playerD{}'.format(i), 'Player D{}'.format(i), 'D')

        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 3, [], include_byes=True)

        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 3)
        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 4)
        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 5)
        for i in range(2, 13):
            db.update_match_by_id(lctx.league_name, 'playerD1', 'playerD{}'.format(i), 5)
        db.update_match_by_id(league_name, 'playerA2', 'playerA1', 3)  # make player a1 lose one game
        db.update_match_by_id(league_name, 'playerC2', 'playerC1', 5)  # make player c1 lose two
        db.update_match_by_id(league_name, 'playerC3', 'playerC1', 5)

        # new season with more sets needed
        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 4, [])
        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 4)
        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 5)
        for i in range(2, 12):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 6)
        for i in range(2, 13):
            db.update_match_by_id(lctx.league_name, 'playerD1', 'playerD{}'.format(i), 7)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('LeAdErBoArD', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('LeAdErBoArD', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('leaderboard stuff', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('leaderboard ', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, leaderboard.handles_message(lctx, CommandMessage(' leaderboard', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, leaderboard.handles_message(lctx, CommandMessage('nothing', 'any_channel', 'any_user', 'any_timestamp')))

    def test_build_post(self):
        sorted_winrates = collections.OrderedDict({
            'p1': {'matches_won': 50, 'matches_lost': 0, 'matches_total': 50, 'games_won': 100, 'games_lost': 0, 'games_total': 100, 'matches_winrate': 100.0, 'games_winrate': 100.1},
            'p2': {'matches_won': 45, 'matches_lost': 5, 'matches_total': 50, 'games_won': 90, 'games_lost': 10, 'games_total': 100, 'matches_winrate': 90.0, 'games_winrate': 90.1},
            'p3': {'matches_won': 40, 'matches_lost': 10, 'matches_total': 50, 'games_won': 80, 'games_lost': 20, 'games_total': 100, 'matches_winrate': 80.0, 'games_winrate': 80.1},
            'p4': {'matches_won': 35, 'matches_lost': 15, 'matches_total': 50, 'games_won': 70, 'games_lost': 30, 'games_total': 100, 'matches_winrate': 70.0, 'games_winrate': 70.1},
            'p5': {'matches_won': 30, 'matches_lost': 20, 'matches_total': 50, 'games_won': 60, 'games_lost': 40, 'games_total': 100, 'matches_winrate': 60.0, 'games_winrate': 60.1},
            'p6': {'matches_won': 25, 'matches_lost': 25, 'matches_total': 50, 'games_won': 50, 'games_lost': 50, 'games_total': 100, 'matches_winrate': 50.0, 'games_winrate': 50.1},
            'p7': {'matches_won': 20, 'matches_lost': 30, 'matches_total': 50, 'games_won': 40, 'games_lost': 60, 'games_total': 100, 'matches_winrate': 40.0, 'games_winrate': 40.1},
            'p8': {'matches_won': 15, 'matches_lost': 35, 'matches_total': 50, 'games_won': 30, 'games_lost': 70, 'games_total': 100, 'matches_winrate': 30.0, 'games_winrate': 30.1},
            'p9': {'matches_won': 10, 'matches_lost': 40, 'matches_total': 50, 'games_won': 20, 'games_lost': 80, 'games_total': 100, 'matches_winrate': 20.0, 'games_winrate': 20.1},
            'p10': {'matches_won': 5, 'matches_lost': 45, 'matches_total': 50, 'games_won': 10, 'games_lost': 90, 'games_total': 100, 'matches_winrate': 10.0, 'games_winrate': 10.1},
            'p11': {'matches_won': 0, 'matches_lost': 50, 'matches_total': 50, 'games_won': 0, 'games_lost': 100, 'games_total': 100, 'matches_winrate': 0.0, 'games_winrate': 0.1}
        })
        result = leaderboard.build_post(sorted_winrates, 'matches', 'winrate')
        expected = '\n p1: 50-0 100.0%\n p2: 45-5 90.0%\n p3: 40-10 80.0%\n p4: 35-15 70.0%\n p5: 30-20 60.0%\n p6: 25-25 50.0%\n p7: 20-30 40.0%\n p8: 15-35 30.0%\n p9: 10-40 20.0%\n p10: 5-45 10.0%'
        self.assertEqual(expected, result)

        result = leaderboard.build_post(sorted_winrates, 'sets', 'winrate')
        expected = '\n p1: 100-0 100.1%\n p2: 90-10 90.1%\n p3: 80-20 80.1%\n p4: 70-30 70.1%\n p5: 60-40 60.1%\n p6: 50-50 50.1%\n p7: 40-60 40.1%\n p8: 30-70 30.1%\n p9: 20-80 20.1%\n p10: 10-90 10.1%'
        self.assertEqual(expected, result)

        result = leaderboard.build_post(sorted_winrates, 'matches', 'won')
        expected = '\n p1: 50\n p2: 45\n p3: 40\n p4: 35\n p5: 30\n p6: 25\n p7: 20\n p8: 15\n p9: 10\n p10: 5'
        self.assertEqual(expected, result)

        result = leaderboard.build_post(sorted_winrates, 'matches', 'played')
        expected = '\n p1: 50\n p2: 50\n p3: 50\n p4: 50\n p5: 50\n p6: 50\n p7: 50\n p8: 50\n p9: 50\n p10: 50'
        self.assertEqual(expected, result)

        result = leaderboard.build_post(sorted_winrates, 'sets', 'won')
        expected = '\n p1: 100\n p2: 90\n p3: 80\n p4: 70\n p5: 60\n p6: 50\n p7: 40\n p8: 30\n p9: 20\n p10: 10'
        self.assertEqual(expected, result)

        result = leaderboard.build_post(sorted_winrates, 'sets', 'played')
        expected = '\n p1: 100\n p2: 100\n p3: 100\n p4: 100\n p5: 100\n p6: 100\n p7: 100\n p8: 100\n p9: 100\n p10: 100'
        self.assertEqual(expected, result)

    def test_get_leaderboard(self):
        result = leaderboard.get_leaderboard(lctx, 'MATCHES', 'WON', True)
        last_result = 999999999
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['matches_won'])
            last_result = result[top_player]['matches_won']
        self.assertIn('Player D1', list(result))

        result = leaderboard.get_leaderboard(lctx, 'MATCHES', 'PLAYED', True)
        last_result = 999999999
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['matches_total'])
            last_result = result[top_player]['matches_total']

        result = leaderboard.get_leaderboard(lctx, 'MATCHES', 'WINRATE', True)
        last_result = 999999999.0
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['matches_winrate'])
            last_result = result[top_player]['matches_winrate']
        self.assertEqual(4, len(list(result)))  # Only A1,B1,C1,D1 have at least 20 matches

        result = leaderboard.get_leaderboard(lctx, 'SETS', 'WON', True)
        last_result = 999999999
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['games_won'])
            last_result = result[top_player]['games_won']

        result = leaderboard.get_leaderboard(lctx, 'SETS', 'PLAYED', True)
        last_result = 999999999
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['games_total'])
            last_result = result[top_player]['games_total']

        result = leaderboard.get_leaderboard(lctx, 'SETS', 'WINRATE', True)
        last_result = 999999999.0
        for top_player in list(result):
            self.assertGreaterEqual(last_result, result[top_player]['games_winrate'])
            last_result = result[top_player]['games_winrate']
        self.assertEqual(4, len(list(result)))  # Only A1,B1,C1,D1 have at least 20 matches

        db.set_active(lctx.league_name, 'playerD1', False)
        result = leaderboard.get_leaderboard(lctx, 'MATCHES', 'WON', True)
        self.assertNotIn('Player D1', list(result))

        result = leaderboard.get_leaderboard(lctx, 'MATCHES', 'WON', False)
        self.assertIn('Player D1', list(result))

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        cases = [
            ['leaderboard', 'MATCHES', 'WON'],
            ['leaderboard matches', 'MATCHES', 'WON'],
            ['leaderboard sets', 'SETS', 'WON'],
            ['leaderboard won', 'MATCHES', 'WON'],
            ['leaderboard played', 'MATCHES', 'PLAYED'],
            ['leaderboard winrate', 'MATCHES', 'WINRATE'],
            ['leaderboard matches played', 'MATCHES', 'PLAYED'],
            ['leaderboard matches won', 'MATCHES', 'WON'],
            ['leaderboard matches winrate', 'MATCHES', 'WINRATE'],
            ['leaderboard sets played', 'SETS', 'PLAYED'],
            ['leaderboard sets won', 'SETS', 'WON'],
            ['leaderboard sets winrate', 'SETS', 'WINRATE']]

        for case in cases:
            mock_post_message.reset_mock()
            msg = CommandMessage(case[0], 'channel', 'any_user', 'any_timestamp')
            leaderboard.handle_message(lctx, msg)
            mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, case[1], case[2], True), case[1], case[2]), 'channel')

        for player in db.get_players(lctx.league_name):
            if player.grouping == 'D':
                db.set_active(lctx.league_name, player.slack_id, False)

        for case in cases:
            mock_post_message.reset_mock()
            msg = CommandMessage(case[0], 'channel', 'any_user', 'any_timestamp')
            leaderboard.handle_message(lctx, msg)
            mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, case[1], case[2], True), case[1], case[2]), 'channel')

        for case in cases:
            mock_post_message.reset_mock()
            msg = CommandMessage(case[0] + ' all', 'channel', 'any_user', 'any_timestamp')
            leaderboard.handle_message(lctx, msg)
            mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, case[1], case[2], False), case[1], case[2]), 'channel')

