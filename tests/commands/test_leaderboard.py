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
            for i in range(1, 10):  # Odd number to get some byes
                db.add_player(lctx.league_name, 'player{}{}'.format(g, i), 'Player {}{}'.format(g, i), g)

        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 3, [], include_byes=True)

        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 3)
        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 4)
        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 5)

        # new season with more sets needed
        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 4, [])
        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 5)
        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 6)
        for i in range(2, 10):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 7)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('LeAdErBoArD', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, leaderboard.handles_message(lctx, CommandMessage('LeAdErBoArD', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, leaderboard.handles_message(lctx, CommandMessage(' leaderboard', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, leaderboard.handles_message(lctx, CommandMessage('leaderboard ', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, leaderboard.handles_message(lctx, CommandMessage('nothing', 'any_channel', 'any_user', 'any_timestamp')))

    def test_build_post(self):
        sorted_winrates = collections.OrderedDict({
            'p1': {'games_won': 100, 'games_lost': 0, 'winrate': 100.0},
            'p2': {'games_won': 90, 'games_lost': 10, 'winrate': 90.0},
            'p3': {'games_won': 80, 'games_lost': 20, 'winrate': 80.0},
            'p4': {'games_won': 70, 'games_lost': 30, 'winrate': 70.0},
            'p5': {'games_won': 60, 'games_lost': 40, 'winrate': 60.0},
            'p6': {'games_won': 50, 'games_lost': 50, 'winrate': 50.0},
            'p7': {'games_won': 40, 'games_lost': 60, 'winrate': 40.0},
            'p8': {'games_won': 30, 'games_lost': 70, 'winrate': 30.0},
            'p9': {'games_won': 20, 'games_lost': 80, 'winrate': 20.0},
            'p10': {'games_won': 10, 'games_lost': 90, 'winrate': 10.0},
            'p11': {'games_won': 0, 'games_lost': 100, 'winrate': 0.0}
        })
        result = leaderboard.build_post(sorted_winrates)
        expected = '\n p1: 100.0% (100-0)\n p2: 90.0% (90-10)\n p3: 80.0% (80-20)\n p4: 70.0% (70-30)\n p5: 60.0% (60-40)\n p6: 50.0% (50-50)\n p7: 40.0% (40-60)\n p8: 30.0% (30-70)\n p9: 20.0% (20-80)\n p10: 10.0% (10-90)'
        self.assertEqual(expected, result)

    def test_get_leaderboard(self):
        result = leaderboard.get_leaderboard(lctx)
        short_result = collections.OrderedDict()
        for top_player in list(result)[:3]:
            short_result[top_player] = result[top_player]
        top_expected = collections.OrderedDict({
            'Player A1': {'games_won': 56, 'games_lost': 8, 'winrate': 87.5},
            'Player B1': {'games_won': 56, 'games_lost': 24, 'winrate': 70.0},
            'Player C1': {'games_won': 56, 'games_lost': 40, 'winrate': 58.33}
        })
        self.assertEqual(top_expected, short_result)

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        msg = CommandMessage('leaderboard', 'channel', 'any_user', 'any_timestamp')
        leaderboard.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, leaderboard.build_post(leaderboard.get_leaderboard(lctx)), 'channel')

