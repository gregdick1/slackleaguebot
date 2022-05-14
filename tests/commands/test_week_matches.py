from unittest import TestCase
from unittest.mock import patch
import datetime
from backend import slack_util, db, match_making
from backend.commands import week_matches
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext
from tests import test_league_setup

lctx = None
player_dictionary = {
    'playerA1': 'Player A1',
    'playerA2': 'Player A2',
    'playerA3': 'Player A3',
    'playerA4': 'Player A4'
}


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()

        league_name = 'test'
        global lctx
        lctx = LeagueContext.load_from_db(league_name)

        db.add_player(lctx.league_name, u'playerA1', 'Player A1', 'A')
        db.add_player(lctx.league_name, u'playerA2', 'Player A2', 'A')
        db.add_player(lctx.league_name, u'playerA3', 'Player A3', 'A')
        db.add_player(lctx.league_name, u'playerA4', 'Player A4', 'A')

        week = datetime.date(2022, 1, 3)
        skip_weeks = []
        match_making.create_matches_for_season(lctx.league_name, week, 3, skip_weeks, False)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_handles_message(self):
        self.assertEqual(True, week_matches.handles_message(lctx, CommandMessage('mAtChEs FoR wEeK', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, week_matches.handles_message(lctx, CommandMessage('mAtChEs FoR wEeK', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(True, week_matches.handles_message(lctx, CommandMessage('WhO dO i PlAy', 'Dchannel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, week_matches.handles_message(lctx, CommandMessage('who do i play', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, week_matches.handles_message(lctx, CommandMessage('matches blah week', 'any_channel', 'any_user', 'any_timestamp')))
        self.assertEqual(False, week_matches.handles_message(lctx, CommandMessage('who play huh', 'any_channel', 'any_user', 'any_timestamp')))

    def test_build_whole_week_message(self):
        matches = db.get_matches_for_week(lctx.league_name, datetime.date(2022, 1, 3))
        players = db.get_players(lctx.league_name)
        result = week_matches.build_whole_week_message(matches, players)
        self.assertEqual(2, result.count('\n'))
        self.assertEqual(1, result.count('Player A1'))
        self.assertEqual(1, result.count('Player A2'))
        self.assertEqual(1, result.count('Player A3'))
        self.assertEqual(1, result.count('Player A4'))

    def test_build_user_week_message(self):
        week = datetime.date(2022, 1, 3)
        matches = db.get_matches_for_week(lctx.league_name, week)
        players = db.get_players(lctx.league_name)
        result = week_matches.build_user_week_message(matches, players, 'playerA1')
        m = [x for x in matches if x.player_1_id == 'playerA1' or x.player_2_id == 'playerA1'][0]
        opp_id = m.player_1_id if m.player_1_id != 'playerA1' else m.player_2_id
        self.assertEqual('\n Playing: {} | week: {}'.format(player_dictionary[opp_id], week), result)

    @patch.object(slack_util, 'post_message')
    def test_handle_message(self, mock_post_message):
        week = datetime.date(2022, 1, 3)
        ts = datetime.datetime(2022, 1, 3).timestamp()
        matches = db.get_matches_for_week(lctx.league_name, week)
        players = db.get_players(lctx.league_name)
        msg = CommandMessage('matches for week', 'channel', 'any_user', str(ts))
        week_matches.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, week_matches.build_whole_week_message(matches, players), 'channel')

        mock_post_message.reset_mock()
        msg = CommandMessage('who do i play', 'Dchannel', 'playerA1', str(ts))
        week_matches.handle_message(lctx, msg)
        mock_post_message.assert_called_once_with(lctx, week_matches.build_user_week_message(matches, players, 'playerA1'), 'Dchannel')
