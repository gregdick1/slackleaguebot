import datetime
from unittest import TestCase
from unittest.mock import patch

from tests import test_league_setup
from tests import doubles_fixture
from backend import db, slack_util, participants
from backend.commands import enter_score, group, help
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext

league_name = 'unittest'


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], datetime.date(2022, 1, 3), 'A', 1, 3)
        db.add_match_by_ids(league_name, self.t['EF'], self.t['GH'], datetime.date(2022, 1, 3), 'B', 1, 3)
        db.add_team(league_name, 2, 'uZ', 'uE', 'A')  # next season's draft team
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def report(self, text, user, channel='comp_channel'):
        with patch.object(slack_util, 'post_message') as post, patch.object(slack_util, 'add_reaction') as react:
            msg = CommandMessage(text, channel, user, 'ts')
            self.assertTrue(enter_score.handles_message(self.lctx, msg), text)
            enter_score.handle_message(self.lctx, msg)
            return post, react

    def match_ab_cd(self):
        return db.get_match_by_participants(league_name, self.t['AB'], self.t['CD'])

    def test_every_member_can_report(self):
        for user, text, winner, p1, p2 in [
            ('uA', 'me over <@uC> 3-1', 'AB', 3, 1),
            ('uB', 'me over <@uD> 3-2', 'AB', 3, 2),
            ('uC', 'me over <@uA> 3-0', 'CD', 0, 3),
            ('uD', '<@uB> over me 3-1', 'AB', 3, 1),
        ]:
            db.clear_score_for_match(league_name, self.match_ab_cd().id)
            post, react = self.report(text, user)
            m = self.match_ab_cd()
            self.assertEqual((self.t[winner], p1, p2), (m.winner_id, m.player_1_score, m.player_2_score), text)
            react.assert_called_once_with(self.lctx, 'comp_channel', 'ts', enter_score.WORKED_REACTION)
            post.assert_called_with(self.lctx, group.build_message_for_group(self.lctx, 'A'), 'comp_channel')

    def test_full_tags_and_duplicates(self):
        self.report('me and <@uB> over <@uC> & <@uD> <@uD> 3-1', 'uA')
        self.assertEqual(self.t['AB'], self.match_ab_cd().winner_id)
        db.clear_score_for_match(league_name, self.match_ab_cd().id)
        self.report('me and <@uA> over <@uC|carol> 3-1', 'uA')
        self.assertEqual(self.t['AB'], self.match_ab_cd().winner_id)

    def assert_rejected(self, text, user, expected, channel='comp_channel'):
        post, react = self.report(text, user, channel)
        post.assert_called_once_with(self.lctx, expected, channel)
        self.assertIsNone(self.match_ab_cd().winner_id)

    def test_rejections(self):
        self.assert_rejected('me over <@uZ> 3-1', 'uA', "<@uZ> isn't on a team this season.")
        self.assert_rejected('me over <@uC> 3-1', 'uZ', "<@uZ> isn't on a team this season.")  # only on a draft team
        self.assert_rejected('me over <@uC> <@uE> 3-1', 'uA', "<@uC> and <@uE> aren't on the same team.")
        self.assert_rejected('me and <@uC> over <@uZ> 3-1', 'uA', "<@uZ> isn't on a team this season.")  # team check runs before split check
        self.assert_rejected('me over <@uB> 3-1', 'uA', "<@uB> is your partner.")
        self.assert_rejected('<@uA> over <@uB> 3-1', 'commish', "<@uA> and <@uB> are on the same team.", channel='Dchannel')
        self.assert_rejected('me over <@uE> 3-1', 'uA', enter_score.NO_MATCH_MSG)
        self.assert_rejected('me over <@uC> 2-0', 'uA', enter_score.get_format_message(self.lctx))
        # sender tagging themselves on both sides
        self.assert_rejected('me over <@uA> 3-1', 'uA', enter_score.PLAYED_YOURSELF_MSG)

    def test_trailing_mention_after_score_records(self):
        # A tag after the score (e.g. partner tagging thanks) must not cause rejection or misparse.
        self.report('me and <@uB> over <@uC> <@uD> 3-1 thanks <@uB>', 'uA')
        self.assertEqual(self.t['AB'], self.match_ab_cd().winner_id)

    def test_hyphenated_label_records(self):
        # labeled mention whose label contains '-' must still record
        self.report('me over <@uC|mary-kate> 3-1', 'uA')
        m = self.match_ab_cd()
        self.assertEqual(self.t['AB'], m.winner_id)

    def test_group_message_uses_match_grouping(self):
        # Moving a team to a different group after scheduling must not change which
        # group update is posted when the match is recorded.
        db.update_team_grouping_and_orders(league_name, [self.t['AB']], 'Z')
        post, _ = self.report('me over <@uC> 3-1', 'uA')
        post.assert_called_with(self.lctx, group.build_message_for_group(self.lctx, 'A'), 'comp_channel')

    def test_admin_dm_entry(self):
        with patch.object(slack_util, 'post_message') as post, patch.object(slack_util, 'add_reaction') as react:
            msg = CommandMessage('<@uD> over <@uA> 3-2', 'Dchannel', 'commish', 'ts')
            self.assertTrue(enter_score.handles_message(self.lctx, msg))
            enter_score.handle_message(self.lctx, msg)
        self.assertEqual(self.t['CD'], self.match_ab_cd().winner_id)
        post.assert_not_called()
        react.assert_called_once_with(self.lctx, 'Dchannel', 'ts', enter_score.WORKED_REACTION)

    def test_help_mentions_either_partner(self):
        self.assertIn('either partner can report', help.channel_help(self.lctx))

    def test_play_all_sets_with_ties(self):
        db.clear_matches_for_season(league_name, 1)
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], datetime.date(2022, 1, 3), 'A', 1, 4, play_all_sets=1)
        self.report('me over <@uC> 2-1-1', 'uA')
        m = self.match_ab_cd()
        self.assertEqual((self.t['AB'], 2, 1, 1, 4), (m.winner_id, m.player_1_score, m.player_2_score, m.tie_score, m.sets))
