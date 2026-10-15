import datetime
import os
import random
from unittest import TestCase
from unittest.mock import patch

import test_league_setup
from backend import db, match_making, utility, slack_util, configs
from backend.commands import group, group_analysis, matchup_history, week_matches, leaderboard, user_stats
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext

league_name = 'unittest'
GOLDEN_DIR = os.path.join(os.path.dirname(__file__), 'golden')


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, 'comp_channel')
        db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commish')
        for g in ['A', 'B']:
            for i in range(1, 5):
                db.add_player(league_name, 'player{}{}'.format(g, i), 'Player {}{}'.format(g, i), g)
        random.seed(20261005)
        match_making.create_matches_for_season(league_name, datetime.date(2022, 1, 3), 3, [], False)
        db.update_match(league_name, 'Player A1', 'Player A2', 3, 1, 0)
        db.update_match(league_name, 'Player A1', 'Player A3', 3, 0, 0)
        db.update_match(league_name, 'Player A4', 'Player A1', 3, 2, 0)
        db.update_match(league_name, 'Player A2', 'Player A3', 3, 2, 0)
        db.update_match(league_name, 'Player B1', 'Player B2', 3, 0, 0)
        db.update_match(league_name, 'Player B3', 'Player B4', 3, 1, 0)
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def assertGolden(self, name, actual):
        path = os.path.join(GOLDEN_DIR, name)
        if os.environ.get('UPDATE_GOLDEN') == '1':
            os.makedirs(GOLDEN_DIR, exist_ok=True)
            with open(path, 'w') as f:
                f.write(actual)
            return
        with open(path) as f:
            self.assertEqual(f.read(), actual)

    def _posted(self, handler, text, channel, user):
        with patch.object(slack_util, 'post_message') as mock_post:
            handler(self.lctx, CommandMessage(text, channel, user, str(datetime.datetime(2022, 1, 3).timestamp())))
            return '\n---\n'.join(c.args[1] for c in mock_post.call_args_list)

    def test_markup(self):
        self.assertGolden('markup_singles.txt', utility.print_season_markup(self.lctx))

    def test_group_message(self):
        self.assertGolden('group_a.txt', group.build_message_for_group(self.lctx, 'A'))

    def test_analyze_group(self):
        self.assertGolden('analyze_group_a.txt', self._posted(group_analysis.handle_message, 'analyze group A', 'comp_channel', 'playerA1'))

    def test_matchup_history(self):
        self.assertGolden('matchup_history_a1.txt', self._posted(matchup_history.handle_message, 'matchup history all', 'Dchannel', 'playerA1'))

    def test_who_do_i_play(self):
        self.assertGolden('who_do_i_play_a1.txt', self._posted(week_matches.handle_message, 'who do i play', 'Dchannel', 'playerA1'))

    def test_leaderboard(self):
        self.assertGolden('leaderboard_all.txt', self._posted(leaderboard.handle_message, 'leaderboard sets won all', 'comp_channel', 'playerA1'))

    def test_user_stats(self):
        self.assertGolden('user_stats_a1.txt', self._posted(user_stats.handle_message, 'my total stats', 'Dchannel', 'playerA1'))
