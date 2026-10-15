import datetime
from unittest import TestCase
from unittest.mock import patch

from tests import test_league_setup
from tests import doubles_fixture
from backend import db, slack_util, utility
from backend.commands import group, group_analysis
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext

league_name = 'unittest'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        week = datetime.date(2022, 1, 3)
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], week, 'A', 1, 3)
        db.add_match_by_ids(league_name, self.t['EF'], self.t['GH'], week, 'B', 1, 3)
        db.update_match_by_participants(league_name, self.t['AB'], self.t['CD'], 3, 1, 0)
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_group_message_shows_team_names(self):
        msg = group.build_message_for_group(self.lctx, 'A')
        self.assertEqual('Group A:\nBob-omb Squad (Alice & Bob) 1-0 (3-1)\nCarol & Dan 0-1 (1-3)', msg)

    def test_markup_has_doubles_standings(self):
        markup = utility.print_season_markup(self.lctx)
        self.assertIn('|Bob-omb Squad (Alice & Bob) 1-0|', markup)  # group B is a 0-0 tie; tie_breaker orders it randomly
        self.assertNotIn('|Bye', markup)
        self.assertIn('Bob-omb Squad (Alice & Bob) - 3<br>Carol & Dan - 1', markup)

    def test_analyze_group_uses_team_names(self):
        # The analyzer expects a real-size group (the singles golden uses 4), so put all 4 teams in a round robin in A.
        db.clear_matches_for_season(league_name, 1)
        ids = [self.t[k] for k in ('AB', 'CD', 'EF', 'GH')]
        db.update_team_grouping_and_orders(league_name, ids, 'A')
        for i in range(4):
            for j in range(i + 1, 4):
                db.add_match_by_ids(league_name, ids[i], ids[j], datetime.date(2022, 1, 3), 'A', 1, 3)
        db.update_match_by_participants(league_name, ids[0], ids[1], 3, 0, 0)
        with patch.object(slack_util, 'post_message') as mock_post:
            group_analysis.handle_message(self.lctx, CommandMessage('analyze group A', 'comp_channel', 'uA', '1'))
        text = mock_post.call_args.args[1]
        self.assertNotIn('Bye', text)
        self.assertTrue(any(name in text for name in ('Bob-omb Squad (Alice & Bob)', 'Carol & Dan', 'Erin & Frank', 'Gina & Hank')), text)


class TestStats(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        w1, w2 = datetime.date(2022, 1, 3), datetime.date(2022, 3, 7)
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], w1, 'A', 1, 3)
        db.update_match_by_participants(league_name, self.t['AB'], self.t['CD'], 3, 1, 0)
        s2_bc = db.add_team(league_name, 2, 'uB', 'uC', 'A')
        s2_ad = db.add_team(league_name, 2, 'uA', 'uD', 'A')
        db.add_match_by_ids(league_name, s2_bc, s2_ad, w2, 'A', 2, 3)
        db.update_match_by_participants(league_name, s2_ad, s2_bc, 3, 2, 0)
        self.s2_bc, self.s2_ad = s2_bc, s2_ad
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def posted(self, handler, text, user, channel='Dchannel', ts=None):
        with patch.object(slack_util, 'post_message') as post:
            handler(self.lctx, CommandMessage(text, channel, user, ts or '1'))
        return post.call_args.args[1]

    def test_my_total_stats_spans_partners(self):
        from backend.commands import user_stats
        self.assertEqual('\n Matches Won: 1 | Matches Lost: 1 | Sets Won: 5 | Sets Lost: 4',
                         self.posted(user_stats.handle_message, 'my total stats', 'uB'))

    def test_matchup_history_counts_each_opponent_never_partner(self):
        from backend.commands import matchup_history
        text = self.posted(matchup_history.handle_message, 'matchup history all', 'uB')
        self.assertIn('Carol: 1-0', text)
        self.assertIn('Dan: 1-1', text)
        self.assertIn('Alice: 0-1', text)
        self.assertNotIn('Bye', text)

    def test_leaderboard_counts_both_members(self):
        from backend.commands import leaderboard
        board = leaderboard.get_leaderboard(self.lctx, 'MATCHES', 'WON', False)
        self.assertEqual({'Alice': 2, 'Bob': 1, 'Carol': 0, 'Dan': 1},
                         {k: v['matches_won'] for k, v in board.items() if k in ('Alice', 'Bob', 'Carol', 'Dan')})

    def test_who_do_i_play(self):
        from backend.commands import week_matches
        ts = str(datetime.datetime(2022, 3, 7).timestamp())
        self.assertEqual('\n Playing: Alice & Dan | week: 2022-03-07',
                         self.posted(week_matches.handle_message, 'who do i play', 'uC', ts=ts))
