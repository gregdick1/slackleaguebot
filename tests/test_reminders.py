from unittest import TestCase
from unittest.mock import call, patch, ANY
from datetime import date, datetime, timedelta

import test_league_setup
from backend import db, reminders, match_making, slack_util, configs
from backend.league_context import LeagueContext

lctx = None
league_name = 'test'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_update_reminders_days(self):
        season = 2
        self.assertEqual(0, len(db.get_reminder_days_for_season(league_name, season)))
        reminders.update_reminders_days(league_name, season, ['2022-01-01T00:00:00Z', '2022-01-02T00:00:00Z'])
        self.assertEqual([
            {'date': date(2022, 1, 1), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 2), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

        reminders.update_reminders_days(league_name, season, ['2022-01-01T00:00:00Z', '2022-01-04T00:00:00Z', '2022-01-02T00:00:00Z'])
        self.assertEqual([
            {'date': date(2022, 1, 1), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 2), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

        reminders.update_reminders_days(league_name, season, ['2022-01-05T00:00:00Z', '2022-01-04T00:00:00Z', '2022-01-02T00:00:00Z'])
        self.assertEqual([
            {'date': date(2022, 1, 2), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 5), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

        reminders.update_reminders_days(league_name, season, ['2022-01-05T00:00:00Z', '2022-01-04T00:00:00Z'])
        self.assertEqual([
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 5), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

        # Set reminders on different season
        reminders.update_reminders_days(league_name, season+1, ['2022-01-05T00:00:00Z', '2022-01-04T00:00:00Z'])
        self.assertEqual([
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season+1},
            {'date': date(2022, 1, 5), 'sent': 0, 'season': season+1},
        ], db.get_reminder_days_for_season(league_name, season+1))

        self.assertEqual([
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 5), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

        # Remove reminders from one season, don't affect the other
        reminders.update_reminders_days(league_name, season + 1, [])
        self.assertEqual([], db.get_reminder_days_for_season(league_name, season + 1))

        self.assertEqual([
            {'date': date(2022, 1, 4), 'sent': 0, 'season': season},
            {'date': date(2022, 1, 5), 'sent': 0, 'season': season},
        ], db.get_reminder_days_for_season(league_name, season))

    @patch.object(slack_util, 'post_message')
    @patch.object(slack_util, 'send_match_messages')
    def test_run_reminders(self, mock_send_match_messages, mock_post_message):
        mock_send_match_messages.return_value = [1, 2, 3]
        today = date.today()
        yesterday = today - timedelta(days=1)

        season = db.get_current_season(league_name)

        db.set_config(league_name, configs.MATCH_MESSAGE, 'match_message')
        db.set_config(league_name, configs.REMINDER_MESSAGE, 'reminder_message')
        db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commissioner')

        # Run without any reminder days in db
        reminders.run_reminders(league_name, debug=True)
        mock_send_match_messages.assert_not_called()
        mock_post_message.assert_not_called()

        # Add old reminder day
        db.add_reminder_day(league_name, season, yesterday)
        reminders.run_reminders(league_name, debug=True)
        mock_send_match_messages.assert_not_called()
        mock_post_message.assert_not_called()

        # Add old reminder day
        db.add_reminder_day(league_name, season, today + timedelta(days=1))
        reminders.run_reminders(league_name, debug=True)
        mock_send_match_messages.assert_not_called()
        mock_post_message.assert_not_called()

        # Add a reminder day for today and run again
        db.add_reminder_day(league_name, season, today)
        reminders.run_reminders(league_name, debug=True)

        calls = [
            call(ANY, 'match_message', today, False, [], debug=True),
            call(ANY, 'reminder_message', yesterday, True, [1, 2, 3], debug=True)
        ]
        mock_send_match_messages.assert_has_calls(calls, any_order=False)
        mock_post_message.assert_called_once_with(ANY, 'Cron Job Reminders Sent: 3 Match Messages, 3 Reminder Messages, Debug=True', 'commissioner')
        days = [x for x in db.get_reminder_days_for_season(league_name, season) if x['date'] == today]
        self.assertEqual([{'date': today, 'sent': 0, 'season': season}], days)

        mock_send_match_messages.reset_mock()
        mock_post_message.reset_mock()

        # Run reminders for real
        reminders.run_reminders(league_name, debug=False)

        calls = [
            call(ANY, 'match_message', today, False, [], debug=False),
            call(ANY, 'reminder_message', yesterday, True, [1, 2, 3], debug=False)
        ]
        mock_send_match_messages.assert_has_calls(calls, any_order=False)
        mock_post_message.assert_called_once_with(ANY, 'Cron Job Reminders Sent: 3 Match Messages, 3 Reminder Messages, Debug=False', 'commissioner')
        days = [x for x in db.get_reminder_days_for_season(league_name, season) if x['date'] == today]
        self.assertEqual([{'date': today, 'sent': 1, 'season': season}], days)

        mock_send_match_messages.reset_mock()
        mock_post_message.reset_mock()

        # Try again and shouldn't run again
        reminders.run_reminders(league_name, debug=True)
        mock_send_match_messages.assert_not_called()
        mock_post_message.assert_not_called()

        reminders.run_reminders(league_name, debug=False)
        mock_send_match_messages.assert_not_called()
        mock_post_message.assert_not_called()
