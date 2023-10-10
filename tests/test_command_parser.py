import datetime
from unittest import TestCase, mock
from unittest.mock import call, patch

import test_league_setup
from backend import command_parser, db, configs
from backend.league_context import LeagueContext

lctx = None


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'test'
        db.set_config(league_name, configs.BOT_SLACK_USER_ID, 'bot_slack_id')
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, 'comp_channel_id')
        global lctx
        lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_validate_and_clean_message(self):
        bot_slack_id = lctx.configs[configs.BOT_SLACK_USER_ID]
        channel_id = lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]

        message_objects = [
            {'text': 'message text', 'channel': channel_id, 'user': 'user'},  # no timestamp
            {'text': 'message text', 'channel': channel_id, 'ts': 'timestamp'},  # no user
            {'text': 'message text', 'user': 'user', 'ts': 'timestamp'},  # no channel
            {'channel': channel_id, 'user': 'user', 'ts': 'timestamp'},  # no text
            {'text': 'message text', 'channel': channel_id, 'user': 'user', 'ts': 'timestamp', 'bot_id': bot_slack_id},  # has bot_id
            {'text': 'message text', 'channel': channel_id, 'user': 'user', 'ts': 'timestamp'},  # message lacks bot id
            {'text': '<@{}> message'.format(bot_slack_id), 'channel': 'fake_channel', 'user': 'user', 'ts': 'timestamp'},  # wrong channel
            {'text': 'message <@{}> text middle'.format(bot_slack_id), 'channel': channel_id, 'user': 'user', 'ts': 'timestamp'},  # bot tag in middle
            {'text': 'message text <@{}> last'.format(bot_slack_id), 'channel': channel_id, 'user': 'user', 'ts': 'timestamp'},  # bot tag at end
        ]
        for m in message_objects:
            result = command_parser.validate_and_clean_message(lctx, m)
            self.assertIsNone(result)

        message_objects = [
            {'text': 'message text', 'channel': 'Dchannel', 'user': 'user', 'ts': 'timestamp'},
            {'text': '<@{}> message text'.format(bot_slack_id), 'channel': 'Dchannel', 'user': 'user', 'ts': 'timestamp'},  # in DM
            {'text': '<@{}> message text'.format(bot_slack_id), 'channel': channel_id, 'user': 'user', 'ts': 'timestamp'}  # in channel
        ]
        for m in message_objects:
            result = command_parser.validate_and_clean_message(lctx, m)
            self.assertEqual('message text', result['text'])

    def test_determine_command(self):
        pass  # TODO
