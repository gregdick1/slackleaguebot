import datetime
from unittest import TestCase, mock
from unittest.mock import call, patch

import test_league_setup
import doubles_fixture
from backend import db, match_making, utility, slack_util, configs
from backend.league_context import LeagueContext

lctx = None


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'unittest'
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
        ids = slack_util.send_match_messages(lctx, 'Match Message @against_user', week, False, [], debug=False)
        mock_send_match_message.assert_not_called()
        self.assertEqual(0, len(ids))

        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, False)

        mock_send_match_message.reset_mock()
        message = 'Match Message @against_user'

        # Call with too early of a date
        early = week - datetime.timedelta(days=1)
        slack_util.send_match_messages(lctx, message, early, False, [], debug=True)
        mock_send_match_message.assert_not_called()
        slack_util.send_match_messages(lctx, message, early, True, [], debug=True)
        mock_send_match_message.assert_not_called()

        # Call day of
        ids = slack_util.send_match_messages(lctx, message, week, False, [], debug=True)
        pd = utility.get_players_dictionary(lctx)
        matches = db.get_matches_for_week(lctx.league_name, week)
        calls = [
            call(lctx, message, matches[0].player_1_id, matches[0].player_2_id, pd, debug=True),
            call(lctx, message, matches[0].player_2_id, matches[0].player_1_id, pd, debug=True),
            call(lctx, message, matches[1].player_1_id, matches[1].player_2_id, pd, debug=True),
            call(lctx, message, matches[1].player_2_id, matches[1].player_1_id, pd, debug=True),
            call(lctx, message, matches[2].player_1_id, matches[2].player_2_id, pd, debug=True),
            call(lctx, message, matches[2].player_2_id, matches[2].player_1_id, pd, debug=True)
        ]
        mock_send_match_message.assert_has_calls(calls, any_order=True)
        self.assertEqual(3, len(ids))
        self.assertEqual(6, mock_send_match_message.call_count)
        self.assertEqual([0, 0, 0], [x.message_sent for x in matches])  # Doesn't set this on debug=true

        # Call day after, should find and send
        mock_send_match_message.reset_mock()
        ids = slack_util.send_match_messages(lctx, message, week+datetime.timedelta(days=1), False, [], debug=True)
        self.assertEqual(3, len(ids))
        self.assertEqual(6, mock_send_match_message.call_count)
        self.assertEqual([0, 0, 0], [x.message_sent for x in matches])  # Doesn't set this on debug=true

        # Call for real, should set message_sent
        mock_send_match_message.reset_mock()
        ids = slack_util.send_match_messages(lctx, message, week, False, [], debug=False)
        matches = db.get_matches_for_week(lctx.league_name, week)
        self.assertEqual(3, len(ids))
        self.assertEqual(6, mock_send_match_message.call_count)
        self.assertEqual([1, 1, 1], [x.message_sent for x in matches])

        # Call again, non-reminders don't send, reminders do
        mock_send_match_message.reset_mock()
        ids = slack_util.send_match_messages(lctx, message, week, False, [], debug=True)
        mock_send_match_message.assert_not_called()
        self.assertEqual(0, len(ids))
        ids = slack_util.send_match_messages(lctx, message, week, True, [], debug=True)
        self.assertEqual(3, len(ids))
        self.assertEqual(6, mock_send_match_message.call_count)

        # Call in the future
        mock_send_match_message.reset_mock()
        ids = slack_util.send_match_messages(lctx, message, week+datetime.timedelta(days=1), True, [], debug=True)
        self.assertEqual(3, len(ids))
        self.assertEqual(6, mock_send_match_message.call_count)

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'send_match_message')
    def test_send_match_messages_and_reminders(self, mock_send_match_message, mock_time_sleep):
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, True)

        message = 'Match Message @against_user'
        sent_match_ids = slack_util.send_match_messages(lctx, message, week+datetime.timedelta(days=1), False, [], False)
        self.assertEqual(3, len(sent_match_ids))
        reminder_match_ids = slack_util.send_match_messages(lctx, message, week+datetime.timedelta(days=1), True, sent_match_ids, False)
        self.assertEqual(0, len(reminder_match_ids))

        reminder_match_ids = slack_util.send_match_messages(lctx, message, week + datetime.timedelta(days=1), True, [], False)
        self.assertEqual(3, len(reminder_match_ids))

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'send_match_message')
    def test_send_match_messages_with_byes(self, mock_send_match_message, mock_time_sleep):
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        db.add_player(lctx.league_name, 'playerA6', 'Player A6', 'A')
        match_making.create_matches_for_season(lctx.league_name, week, 1, skip_weeks, True)

        message = 'Match Message @against_user'
        # Future call, should still find matches to send non-reminders
        slack_util.send_match_messages(lctx, message, week + datetime.timedelta(days=1), False, [], debug=False)
        pd = utility.get_players_dictionary(lctx)
        matches = db.get_matches_for_week(lctx.league_name, week)
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
        self.assertEqual([1, 1, 1, 1], [x.message_sent for x in matches])

        # Call again, no reminders for bye match
        mock_send_match_message.reset_mock()
        slack_util.send_match_messages(lctx, message, week, True, [], debug=True)
        self.assertEqual(6, mock_send_match_message.call_count)

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


class TestDoublesMessages(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        week = datetime.date(2022, 1, 3)
        db.add_match_by_ids('unittest', self.t['AB'], self.t['CD'], week, 'A', 1, 3)
        db.add_match_by_ids('unittest', self.t['EF'], None, week, 'B', 1, 3)
        self.lctx = LeagueContext.load_from_db('unittest')
        self.week = week

    def tearDown(self):
        test_league_setup.teardown_test_league()

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'post_message')
    def test_four_dms_per_match_and_two_for_bye(self, mock_post, _sleep):
        message = 'You and @partner_user vs @against_user'
        slack_util.send_match_messages(self.lctx, message, self.week, False, [], debug=False)
        sent = {c.args[2]: c.args[1] for c in mock_post.call_args_list}
        self.assertEqual('You and <@uB> vs <@uC> & <@uD>', sent['uA'])
        self.assertEqual('You and <@uA> vs <@uC> & <@uD>', sent['uB'])
        self.assertEqual('You and <@uD> vs Bob-omb Squad (<@uA> & <@uB>)', sent['uC'])
        self.assertEqual('You and <@uC> vs Bob-omb Squad (<@uA> & <@uB>)', sent['uD'])
        bye = 'This week, you have a bye. Relax and get some practice in.'
        self.assertEqual((bye, bye), (sent['uE'], sent['uF']))
        self.assertEqual(6, mock_post.call_count)

    @patch.object(slack_util, 'post_message')
    def test_debug_output_names_recipients(self, mock_post):
        out = slack_util.send_match_message(self.lctx, 'vs @against_user', 'uA', self.t['CD'], utility.get_players_dictionary(self.lctx), debug=True)
        self.assertEqual('Debug sent to Alice: vs <@Carol> & <@Dan>', out)
        mock_post.assert_not_called()

    @patch('time.sleep', return_value=None)
    @patch.object(slack_util, 'post_message')
    def test_custom_messages_only_current_team_members(self, mock_post, _sleep):
        slack_util.send_custom_messages(self.lctx, 'hi', debug=False)
        self.assertEqual(['uA', 'uB', 'uC', 'uD', 'uE', 'uF', 'uG', 'uH'], sorted(c.args[2] for c in mock_post.call_args_list))

    @patch.object(slack_util, 'post_message')
    def test_singles_strips_partner_variable(self, mock_post):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        db.add_player('unittest', 'p1', 'P1', 'A')
        db.add_player('unittest', 'p2', 'P2', 'A')
        lctx = LeagueContext.load_from_db('unittest')
        slack_util.send_match_message(lctx, 'Partner:@partner_user vs @against_user', 'p1', 'p2', utility.get_players_dictionary(lctx), debug=False)
        mock_post.assert_called_once_with(lctx, 'Partner: vs <@p2>', 'p1')

