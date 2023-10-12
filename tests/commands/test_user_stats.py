import datetime
from unittest import TestCase
from unittest.mock import patch

from backend import slack_util, db, match_making
from backend.commands import user_stats
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
            for i in range(1, 9):
                db.add_player(lctx.league_name, 'player{}{}'.format(g, i), 'Player {}{}'.format(g, i), g)

        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 3, [])

        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 3, 0, 0)
        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 3, 1, 0)
        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 3, 2, 0)

        # new season with more sets needed
        match_making.create_matches_for_season(lctx.league_name, datetime.date(2022, 1, 3), 4, [])
        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA{}'.format(i), 4, 1, 0)
        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB{}'.format(i), 4, 2, 0)
        for i in range(2, 9):
            db.update_match_by_id(lctx.league_name, 'playerC1', 'playerC{}'.format(i), 4, 3, 0)

    def test_handles_message(self):
        self.assertEqual(True, user_stats.handles_message(lctx, CommandMessage('My ToTaL StAtS', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, user_stats.handles_message(lctx, CommandMessage('My ToTaL StAtS', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, user_stats.handles_message(lctx, CommandMessage('a my total stats', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, user_stats.handles_message(lctx, CommandMessage('my total stats and more', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, user_stats.handles_message(lctx, CommandMessage('just stats', 'any_channel', 'any_user', 'any_timestamp')))

    def test_build_stat_message(self):
        matches = db.get_matches(lctx.league_name)
        result = user_stats.build_stat_message(matches, 'playerA1')
        self.assertEqual('\n Matches Won: 14 | Matches Lost: 0 | Sets Won: 49 | Sets Lost: 7', result)

        result = user_stats.build_stat_message(matches, 'playerA2')
        self.assertEqual('\n Matches Won: 0 | Matches Lost: 2 | Sets Won: 1 | Sets Lost: 7', result)

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        matches = db.get_matches(lctx.league_name)
        msg = CommandMessage('help', 'Dchannel', 'playerA1', 'any_timestamp')
        user_stats.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, user_stats.build_stat_message(matches, 'playerA1'), 'Dchannel')
