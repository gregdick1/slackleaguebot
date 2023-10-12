import datetime
from unittest import TestCase

import test_league_setup
from backend import db, match_making, utility, configs
from backend.league_context import LeagueContext

league_name = 'unittest'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_gather_scores(self):
        db.add_player(league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(league_name, u'playerA4', 'Player A4', 'A')
        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(league_name, week, 4, skip_weeks, False, False)

        db.update_match(league_name, 'Player A1', 'Player A2', 4)
        db.update_match(league_name, 'Player A1', 'Player A3', 5)
        db.update_match(league_name, 'Player A1', 'Player A4', 6)
        db.update_match(league_name, 'Player A3', 'Player A2', 7)
        db.update_match(league_name, 'Player A4', 'Player A2', 6)
        db.update_match(league_name, 'Player A4', 'Player A3', 5)

        matches = db.get_matches(league_name)
        results = utility.gather_scores(matches)
        self.assertEqual(results[0], {'player_id': 'playerA1', 'm_w': 3, 'm_l': 0, 's_w': 12, 's_l': 3})
        self.assertEqual(results[1], {'player_id': 'playerA4', 'm_w': 2, 'm_l': 1, 's_w': 10, 's_l': 7})
        self.assertEqual(results[2], {'player_id': 'playerA3', 'm_w': 1, 'm_l': 2, 's_w': 6, 's_l': 11})
        self.assertEqual(results[3], {'player_id': 'playerA2', 'm_w': 0, 'm_l': 3, 's_w': 5, 's_l': 12})

    def test_replace_message_variables(self):
        message = 'stuff @bot_name and #competition_channel stuff'
        db.set_config(league_name, configs.BOT_SLACK_USER_ID, 'bot_slack_id')
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, 'channel_slack_id')
        lctx = LeagueContext.load_from_db(league_name)

        self.assertEqual('stuff <@bot_slack_id> and <#channel_slack_id> stuff', utility.replace_message_variables(lctx, message))

        message = 'does not include any of the variables'
        self.assertEqual(message, utility.replace_message_variables(lctx, message))

    # TODO test the printout function