from unittest import TestCase
from unittest.mock import patch

from backend import slack_util
from backend.commands import help
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

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, help.handles_message(lctx, CommandMessage('help', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, help.handles_message(lctx, CommandMessage('help', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, help.handles_message(lctx, CommandMessage('HeLp', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, help.handles_message(lctx, CommandMessage('help more stuff', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, help.handles_message(lctx, CommandMessage('stuff then help', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, help.handles_message(lctx, CommandMessage('no hlp', 'any_channel', 'any_user', 'any_timestamp')))

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        msg = CommandMessage('help', 'channel', 'any_user', 'any_timestamp')
        help.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, help.channel_help(lctx), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('help', 'Dchannel', 'any_user', 'any_timestamp')
        help.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, help.dm_help(lctx), 'Dchannel')
