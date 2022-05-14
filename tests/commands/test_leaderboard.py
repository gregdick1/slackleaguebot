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

        league_name = 'test'
        global lctx
        lctx = LeagueContext.load_from_db(league_name)

        for g in ['A', 'B', 'C']:
            for i in range(1, 12):  # Odd number to get some byes
                db.add_player(lctx.league_name, 'player{}{}'.format(g, i), 'Player {}{}'.format(g, i), g)
        for i in range(1, 13):
            db.add_player(lctx.league_name, 'playerD{}'.format(i), 'Player D{}'.format(i), g)

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
            'p1': {'matches_won': 50, 'matches_lost': 0, 'games_won': 100, 'games_lost': 0, 'winrate': 100.0},
            'p2': {'matches_won': 45, 'matches_lost': 5, 'games_won': 90, 'games_lost': 10, 'winrate': 90.0},
            'p3': {'matches_won': 40, 'matches_lost': 10, 'games_won': 80, 'games_lost': 20, 'winrate': 80.0},
            'p4': {'matches_won': 35, 'matches_lost': 15, 'games_won': 70, 'games_lost': 30, 'winrate': 70.0},
            'p5': {'matches_won': 30, 'matches_lost': 20, 'games_won': 60, 'games_lost': 40, 'winrate': 60.0},
            'p6': {'matches_won': 25, 'matches_lost': 25, 'games_won': 50, 'games_lost': 50, 'winrate': 50.0},
            'p7': {'matches_won': 20, 'matches_lost': 30, 'games_won': 40, 'games_lost': 60, 'winrate': 40.0},
            'p8': {'matches_won': 15, 'matches_lost': 35, 'games_won': 30, 'games_lost': 70, 'winrate': 30.0},
            'p9': {'matches_won': 10, 'matches_lost': 40, 'games_won': 20, 'games_lost': 80, 'winrate': 20.0},
            'p10': {'matches_won': 5, 'matches_lost': 45, 'games_won': 10, 'games_lost': 90, 'winrate': 10.0},
            'p11': {'matches_won': 0, 'matches_lost': 50, 'games_won': 0, 'games_lost': 100, 'winrate': 0.0}
        })
        result = leaderboard.build_post(sorted_winrates)
        expected = '\n p1: 50-0 (100-0) 100.0%\n p2: 45-5 (90-10) 90.0%\n p3: 40-10 (80-20) 80.0%\n p4: 35-15 (70-30) 70.0%\n p5: 30-20 (60-40) 60.0%\n p6: 25-25 (50-50) 50.0%\n p7: 20-30 (40-60) 40.0%\n p8: 15-35 (30-70) 30.0%\n p9: 10-40 (20-80) 20.0%\n p10: 5-45 (10-90) 10.0%'
        self.assertEqual(expected, result)

    def test_get_leaderboard(self):
        result = leaderboard.get_leaderboard(lctx, 'MaTcHeS')
        short_result = collections.OrderedDict()
        for top_player in list(result)[:4]:
            short_result[top_player] = result[top_player]
        top_expected = collections.OrderedDict({
            'Player D1': {'matches_won': 22, 'matches_lost': 0, 'games_won': 77, 'games_lost': 55, 'winrate': 58.33},
            'Player B1': {'matches_won': 20, 'matches_lost': 0, 'games_won': 70, 'games_lost': 20, 'winrate': 77.78},
            'Player A1': {'matches_won': 19, 'matches_lost': 1, 'games_won': 67, 'games_lost': 3, 'winrate': 95.71},
            'Player C1': {'matches_won': 18, 'matches_lost': 2, 'games_won': 68, 'games_lost': 42, 'winrate': 61.82}
        })
        self.assertEqual(top_expected, short_result)

        result = leaderboard.get_leaderboard(lctx, '')
        short_result = collections.OrderedDict()
        for top_player in list(result)[:4]:
            short_result[top_player] = result[top_player]
        self.assertEqual(top_expected, short_result)

        result = leaderboard.get_leaderboard(lctx, 'SeTs')
        short_result = collections.OrderedDict()
        for top_player in list(result)[:4]:
            short_result[top_player] = result[top_player]
        top_expected = collections.OrderedDict({
            'Player D1': {'matches_won': 22, 'matches_lost': 0, 'games_won': 77, 'games_lost': 55, 'winrate': 58.33},
            'Player B1': {'matches_won': 20, 'matches_lost': 0, 'games_won': 70, 'games_lost': 20, 'winrate': 77.78},
            'Player C1': {'matches_won': 18, 'matches_lost': 2, 'games_won': 68, 'games_lost': 42, 'winrate': 61.82},
            'Player A1': {'matches_won': 19, 'matches_lost': 1, 'games_won': 67, 'games_lost': 3, 'winrate': 95.71}
        })
        self.assertEqual(top_expected, short_result)

        result = leaderboard.get_leaderboard(lctx, 'wInRaTe')
        short_result = collections.OrderedDict()
        for top_player in list(result)[:4]:
            short_result[top_player] = result[top_player]
        top_expected = collections.OrderedDict({
            'Player A1': {'matches_won': 19, 'matches_lost': 1, 'games_won': 67, 'games_lost': 3, 'winrate': 95.71},
            'Player B1': {'matches_won': 20, 'matches_lost': 0, 'games_won': 70, 'games_lost': 20, 'winrate': 77.78},
            'Player C1': {'matches_won': 18, 'matches_lost': 2, 'games_won': 68, 'games_lost': 42, 'winrate': 61.82},
            'Player D1': {'matches_won': 22, 'matches_lost': 0, 'games_won': 77, 'games_lost': 55, 'winrate': 58.33}
        })
        self.assertEqual(top_expected, short_result)

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        msg = CommandMessage('leaderboard', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, '')), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('leaderboard matches', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, 'matches')), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('leaderboard sets', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, 'sets')), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('leaderboard winrate', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx, 'winrate')), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('leaderboard winrate garbage', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.BAD_OPTION_MSG, 'channel')
