from unittest import TestCase
from unittest.mock import patch
import datetime

from backend import slack_util, db, match_making
from backend.commands import group
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

        db.add_player(lctx.league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(lctx.league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(lctx.league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(lctx.league_name, u'playerA4', 'Player A4', 'A')
        db.add_player(lctx.league_name, u'playerB1', 'Player B1', 'B')
        db.add_player(lctx.league_name, u'playerB2', 'Player B2', 'B')
        db.add_player(lctx.league_name, u'playerB3', 'Player B3', 'B')
        db.add_player(lctx.league_name, u'playerB4', 'Player B4', 'B')
        db.add_player(lctx.league_name, u'playerB5', 'Player B5', 'B')

        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 3, skip_weeks, True)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, group.handles_message(lctx, CommandMessage('group a', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, group.handles_message(lctx, CommandMessage('group a', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, group.handles_message(lctx, CommandMessage('GrOuP B', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, group.handles_message(lctx, CommandMessage('GROUP Bextra', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, group.handles_message(lctx, CommandMessage('anything group', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, group.handles_message(lctx, CommandMessage('group', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, group.handles_message(lctx, CommandMessage('no grp', 'any_channel', 'any_user', 'any_timestamp')))

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        msg = CommandMessage('group bextra', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, group.MISFORMAT_MSG, 'any_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('group ', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, group.MISFORMAT_MSG, 'any_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('group C', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, group.NOT_A_GROUP_MSG, 'any_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('group b', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once()

        db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA2', 3, 2, 0)
        db.update_match_by_id(lctx.league_name, 'playerA1', 'playerA3', 3, 1, 0)
        db.update_match_by_id(lctx.league_name, 'playerA2', 'playerA3', 3, 0, 0)
        printout = 'Group A:\nPlayer A1 2-0 (6-3)\nPlayer A2 1-1 (5-3)\nPlayer A3 0-2 (1-6)\nPlayer A4 0-0 (0-0)'

        mock_post_message.reset_mock()
        msg = CommandMessage('GrOuP A', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, printout, 'any_channel')

        # No 'Bye' player in printout
        db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB2', 3, 2, 0)
        db.update_match_by_id(lctx.league_name, 'playerB1', 'playerB3', 3, 1, 0)
        db.update_match_by_id(lctx.league_name, 'playerB2', 'playerB3', 3, 0, 0)
        db.update_match_by_id(lctx.league_name, 'playerB5', 'playerB4', 0, 3, 0)
        printout = 'Group B:\nPlayer B1 2-0 (6-3)\nPlayer B2 1-1 (5-3)\nPlayer B5 1-0 (3-0)\nPlayer B3 0-2 (1-6)\nPlayer B4 0-1 (0-3)'

        mock_post_message.reset_mock()
        msg = CommandMessage('GrOuP B', 'any_channel', 'any_user', 'any_timestamp')
        group.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, printout, 'any_channel')
        