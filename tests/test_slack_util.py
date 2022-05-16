import datetime
from unittest import TestCase, mock
from unittest.mock import call, patch

import test_league_setup
from backend import db, match_making, utility, slack_util, configs
from backend.league_context import LeagueContext

lctx = None


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'test'
        db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commissioner_slack_id')
        global lctx
        lctx = LeagueContext.load_from_db(league_name)

        db.add_player(lctx.league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(lctx.league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(lctx.league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(lctx.league_name, u'playerA4', 'Player A4', 'A')
        db.add_player(lctx.league_name, u'playerA5', 'Player A5', 'A')
        db.add_player(lctx.league_name, u'commissioner_slack_id', 'Commissioner', 'A')

    def tearDown(self):
        test_league_setup.teardown_test_league()
        global lctx
        lctx = None

    @patch.object(slack_util, '_get_users_list')
    def test_get_slack_id(self, mock_get_users_list):
        mock_get_users_list.return_value = [{'profile': {'real_name': 'John Smith'}, 'id': 'slack_id', 'deleted': False}]
        result = slack_util.get_slack_id(lctx, 'John Smith')
        self.assertEqual('slack_id', result)

    @patch.object(slack_util, '_get_users_list')
    def test_get_deactivated_slack_ids(self, mock_get_users_list):
        mock_get_users_list.return_value = [
            {'profile': {'real_name': 'John Smith1'}, 'id': 'playerA1', 'deleted': False},
            {'profile': {'real_name': 'John Smith2'}, 'id': 'playerA2', 'deleted': True},
            {'profile': {'real_name': 'John Smith3'}, 'id': 'playerA3', 'deleted': True},
            {'profile': {'real_name': 'John Smith4'}, 'id': 'playerA4', 'deleted': True},
            {'profile': {'real_name': 'John Smith5'}, 'id': 'playerA5', 'deleted': False}]
        result = slack_util.get_deactivated_slack_ids(lctx)
        self.assertEqual(['playerA2', 'playerA3', 'playerA4'], result)

    @patch.object(slack_util, 'post_message')
    def test_send_match_message(self, mock_post_message):
        slack_util.send_match_message(lctx, 'Match Message @against_user', 'playerA2', 'playerA1', utility.get_players_dictionary(lctx), debug=False)
        mock_post_message.assert_called_once_with(lctx, 'Match Message <@playerA1>', 'playerA2')

        mock_post_message.reset_mock()
        slack_util.send_match_message(lctx, 'Match Message @against_user', 'playerA2', 'playerA1', utility.get_players_dictionary(lctx), debug=True)
        mock_post_message.assert_not_called()

        mock_post_message.reset_mock()
        slack_util.send_match_message(lctx, 'Match Message @against_user', 'commissioner_slack_id', 'playerA1', utility.get_players_dictionary(lctx), debug=True)
        mock_post_message.assert_called_once_with(lctx, 'Match Message <@playerA1>', 'commissioner_slack_id')

        mock_post_message.reset_mock()
        return_val = slack_util.send_match_message(lctx, 'Match Message @against_user', 'playerA2', None, utility.get_players_dictionary(lctx), debug=False)
        mock_post_message.assert_called_once_with(lctx, 'This week, you have a bye. Relax and get some practice in.', 'playerA2')
        self.assertIsNotNone(return_val)

        mock_post_message.reset_mock()
        return_val = slack_util.send_match_message(lctx, 'Match Message @against_user', None, 'playerA2', utility.get_players_dictionary(lctx), debug=False)
        mock_post_message.assert_not_called()
        self.assertIsNotNone(return_val)

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'send_match_message')
    def test_send_match_messages(self, mock_send_match_message, mock_time_sleep):
        week = datetime.date(2022, 1, 3)
        slack_util.send_match_messages(lctx, 'Match Message @against_user', week, debug=False)
        mock_send_match_message.assert_not_called()

        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, False)
        matches = db.get_matches_for_week(lctx.league_name, week)

        mock_send_match_message.reset_mock()
        message = 'Match Message @against_user'
        slack_util.send_match_messages(lctx, message, week, debug=True)
        pd = utility.get_players_dictionary(lctx)
        calls = [
            call(lctx, message, matches[0].player_1_id, matches[0].player_2_id, pd, debug=True),
            call(lctx, message, matches[0].player_2_id, matches[0].player_1_id, pd, debug=True),
            call(lctx, message, matches[1].player_1_id, matches[1].player_2_id, pd, debug=True),
            call(lctx, message, matches[1].player_2_id, matches[1].player_1_id, pd, debug=True),
            call(lctx, message, matches[2].player_1_id, matches[2].player_2_id, pd, debug=True),
            call(lctx, message, matches[2].player_2_id, matches[2].player_1_id, pd, debug=True)
        ]
        mock_send_match_message.assert_has_calls(calls, any_order=True)
        self.assertEqual(6, mock_send_match_message.call_count)

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'send_match_message')
    def test_send_match_messages_with_byes(self, mock_send_match_message, mock_time_sleep):
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        db.add_player(lctx.league_name, 'playerA6', 'Player A6', 'A')
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, True)
        matches = db.get_matches_for_week(lctx.league_name, week)

        message = 'Match Message @against_user'
        slack_util.send_match_messages(lctx, message, week, debug=False)
        pd = utility.get_players_dictionary(lctx)
        calls = [
            call(lctx, message, matches[0].player_1_id, None, pd, debug=False),
            call(lctx, message, None, matches[0].player_1_id, pd, debug=False),
            call(lctx, message, matches[1].player_1_id, matches[1].player_2_id, pd, debug=False),
            call(lctx, message, matches[1].player_2_id, matches[1].player_1_id, pd, debug=False),
            call(lctx, message, matches[2].player_1_id, matches[2].player_2_id, pd, debug=False),
            call(lctx, message, matches[2].player_2_id, matches[2].player_1_id, pd, debug=False),
            call(lctx, message, matches[3].player_1_id, matches[3].player_2_id, pd, debug=False),
            call(lctx, message, matches[3].player_2_id, matches[3].player_1_id, pd, debug=False)
        ]
        mock_send_match_message.assert_has_calls(calls, any_order=True)
        self.assertEqual(8, mock_send_match_message.call_count)

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'post_message')
    def test_send_custom_messages(self, mock_post_message, mock_time_sleep):
        db.set_active(lctx.league_name, 'playerA3', False)
        message = 'Custom message'
        slack_util.send_custom_messages(lctx, message, debug=False)
        calls = [
            call(lctx, message, 'playerA1'),
            call(lctx, message, 'playerA2'),
            call(lctx, message, 'playerA4'),
            call(lctx, message, 'playerA5'),
            call(lctx, message, 'commissioner_slack_id'),
        ]
        mock_post_message.assert_has_calls(calls)
        self.assertEqual(5, mock_post_message.call_count)

        mock_post_message.reset_mock()
        slack_util.send_custom_messages(lctx, message, debug=True)
        mock_post_message.assert_called_once_with(lctx, message, 'commissioner_slack_id')

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'post_message')
    def test_send_custom_for_missed_games(self, mock_post_message, mock_time_sleep):
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, False)
        matches = db.get_matches_for_week(lctx.league_name, week)
        db.update_match_by_id(lctx.league_name, matches[0].player_1_id, matches[0].player_2_id, 1)

        message = 'Play your games!'
        slack_util.send_custom_for_missed_games(lctx, message, 3, datetime.date(2022, 1, 17), debug=False)
        calls = [
            call(lctx, message, matches[1].player_1_id),
            call(lctx, message, matches[1].player_2_id),
            call(lctx, message, matches[2].player_1_id),
            call(lctx, message, matches[2].player_2_id),
        ]
        mock_post_message.assert_has_calls(calls)
        self.assertEqual(4, mock_post_message.call_count)

        mock_post_message.reset_mock()
        slack_util.send_custom_for_missed_games(lctx, message, 2, datetime.date(2022, 1, 17), debug=True)  # change num_missed to 2 to ensure commissioner missed 2
        mock_post_message.assert_called_once_with(lctx, message, 'commissioner_slack_id')
