from unittest import TestCase
from unittest.mock import patch, call
import datetime, time

from backend import slack_util, configs, db, match_making
from backend.commands import enter_score, group
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext
from tests import test_league_setup

lctx = None


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'test'
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, 'comp_channel')
        db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commish')

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

        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 3, skip_weeks, True)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, enter_score.handles_message(lctx, CommandMessage('mE oVeR <@playerA1>', 'comp_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, enter_score.handles_message(lctx, CommandMessage('mE oVeR <@playerA1> blah', 'comp_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, enter_score.handles_message(lctx, CommandMessage('<@playerA1> OvEr Me', 'comp_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, enter_score.handles_message(lctx, CommandMessage('<@playerA1> OvEr Me blah', 'comp_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, enter_score.handles_message(lctx, CommandMessage('<@playerA1> OvEr <@playerA2>', 'Dchannel', 'commish', 'any_timestamp')))
        self.assertEqual(False, enter_score.handles_message(lctx, CommandMessage('<@playerA1> OvEr <@playerA2>', 'comp_channel', 'commish', 'any_timestamp')))
        self.assertEqual(False, enter_score.handles_message(lctx, CommandMessage('<@playerA1> OvEr <@playerA2>', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, enter_score.handles_message(lctx, CommandMessage('me over playerA2', 'comp_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, enter_score.handles_message(lctx, CommandMessage('playerA2 over me', 'any_channel', 'any_user', 'any_timestamp')))

    @patch.object(slack_util, 'post_message')
    def test_handle_message_parse_user(self, mock_post_message):
        msg = CommandMessage('garbage command', 'comp_channel', 'any_user', 'any_timestamp')  # shouldn't actually be possible for this to make it in, but it has a code path
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('me over <@playerA1>', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.PLAYED_YOURSELF_MSG, 'comp_channel')
        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA1> over me', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.PLAYED_YOURSELF_MSG, 'comp_channel')

    @patch.object(slack_util, 'post_message')
    def test_handle_message_finding_match(self, mock_post_message):
        msg = CommandMessage('<@playerB1> over me', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.NO_MATCH_MSG, 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('me over <@playerB1>', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.NO_MATCH_MSG, 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerB1> over <@playerA1>', 'Dchannel', 'commish', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.NO_MATCH_MSG, 'Dchannel')

    @patch.object(slack_util, 'post_message')
    def test_handle_message_parse_score(self, mock_post_message):
        msg = CommandMessage('<@playerA2> over me blah', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me 3 2', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me a-b', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me 2-0', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me 3-3', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me 4-0', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over me 2-1', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, enter_score.get_format_message(lctx), 'comp_channel')

    @patch.object(slack_util, 'add_reaction')
    @patch.object(slack_util, 'post_message')
    def test_handle_message_good_entry(self, mock_post_message, mock_add_reaction):
        msg = CommandMessage('<@playerA2> over me 3-1', 'comp_channel', 'playerA1', 'any_timestamp')
        lctx.configs[configs.MESSAGE_COMMISSIONER_ON_SUCCESS] = 'TRUE'
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA2']
        self.assertEqual(1, len(tmp))
        self.assertEqual(4, tmp[0].sets)

        mock_add_reaction.assert_called_once_with(lctx, 'comp_channel', 'any_timestamp', enter_score.WORKED_REACTION)
        group_msg = group.build_message_for_group(lctx, 'A')
        calls = [
            call(lctx, 'Entered into db', 'commish'),
            call(lctx, group_msg, 'comp_channel')
        ]
        mock_post_message.assert_has_calls(calls)

        mock_add_reaction.reset_mock()
        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA1> over <@playerA2> 3-2', 'Dchannel', 'commish', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA1']
        self.assertEqual(1, len(tmp))
        self.assertEqual(5, tmp[0].sets)

        mock_add_reaction.assert_called_once_with(lctx, 'Dchannel', 'any_timestamp', enter_score.WORKED_REACTION)
        mock_post_message.assert_not_called()

    @patch.object(slack_util, 'add_reaction')
    @patch.object(slack_util, 'post_message')
    def test_handle_message_no_sets(self, mock_post_message, mock_add_reaction):
        week = datetime.date(2022, 1, 24)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, True)

        msg = CommandMessage('<@playerA2> over me', 'comp_channel', 'playerA1', 'any_timestamp')
        lctx.configs[configs.MESSAGE_COMMISSIONER_ON_SUCCESS] = 'TRUE'
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA2']
        self.assertEqual(1, len(tmp))
        self.assertEqual(1, tmp[0].sets)

        mock_add_reaction.assert_called_once_with(lctx, 'comp_channel', 'any_timestamp', enter_score.WORKED_REACTION)
        group_msg = group.build_message_for_group(lctx, 'A')
        calls = [
            call(lctx, 'Entered into db', 'commish'),
            call(lctx, group_msg, 'comp_channel')
        ]
        mock_post_message.assert_has_calls(calls)

        mock_add_reaction.reset_mock()
        mock_post_message.reset_mock()
        msg = CommandMessage('me over <@playerA2>', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA1']
        self.assertEqual(1, len(tmp))
        self.assertEqual(1, tmp[0].sets)

        mock_add_reaction.assert_called_once_with(lctx, 'comp_channel', 'any_timestamp', enter_score.WORKED_REACTION)
        group_msg = group.build_message_for_group(lctx, 'A')
        calls = [
            call(lctx, 'Entered into db', 'commish'),
            call(lctx, group_msg, 'comp_channel')
        ]
        mock_post_message.assert_has_calls(calls)

        mock_add_reaction.reset_mock()
        mock_post_message.reset_mock()
        msg = CommandMessage('<@playerA2> over <@playerA1>', 'Dchannel', 'commish', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA2']
        self.assertEqual(1, len(tmp))
        self.assertEqual(1, tmp[0].sets)

        mock_add_reaction.assert_called_once_with(lctx, 'Dchannel', 'any_timestamp', enter_score.WORKED_REACTION)
        mock_post_message.assert_not_called()

    @patch.object(db, 'update_match_by_id', side_effect = Exception('test'))
    @patch.object(slack_util, 'add_reaction')
    @patch.object(slack_util, 'post_message')
    def test_handle_message_enter_score_error(self, mock_post_message, mock_add_reaction, mock_update_match):
        msg = CommandMessage('<@playerA2> over me 3-1', 'comp_channel', 'playerA1', 'any_timestamp')
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA2']
        self.assertEqual(0, len(tmp))

        mock_post_message.assert_called_once_with(lctx, 'Failed to enter into db', 'commish')
        mock_add_reaction.assert_called_once_with(lctx, 'comp_channel', 'any_timestamp', enter_score.NOT_WORKED_REACTION)

    @patch.object(slack_util, 'add_reaction')
    @patch.object(slack_util, 'post_message')
    def test_handle_message_blocked_scores(self, mock_post_message, mock_add_reaction):
        msg = CommandMessage('<@playerA2> over me 3-1', 'comp_channel', 'playerA1', 'any_timestamp')
        lctx.configs[configs.BLOCK_NEW_SCORES] = 'TRUE'
        enter_score.handle_message(lctx, msg)
        matches = db.get_matches(lctx.league_name)
        tmp = [x for x in matches if x.winner_id == 'playerA2']
        self.assertEqual(0, len(tmp))

        mock_post_message.assert_called_once_with(lctx, enter_score.BLOCK_NEW_SCORES_MSG, 'comp_channel')