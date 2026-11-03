import datetime
from unittest import TestCase, mock
from unittest.mock import patch

from tests import test_league_setup, doubles_fixture
from backend import command_parser, configs, db, leaguebot, match_making, slack_util
from backend.commands import enter_score
from backend.commands.command_message import CommandMessage
from backend.league_context import LeagueContext

league_name = 'unittest'
# The real league bot IDs that hudl/ssb-streaming hardcodes in server/score-report.ts
SINGLES_BOT = 'U06095NFANT'
DOUBLES_BOT = 'U0CA1H1LC4Q'
STREAMBOT_USER = 'USTREAMBOT'
STREAMBOT_BOT_ID = 'BSTREAMBOT'
CHANNEL = 'comp_channel'


def bot_event(text, bot_id=STREAMBOT_BOT_ID, user=STREAMBOT_USER, channel=CHANNEL, ts='1'):
    event = {'text': text, 'channel': channel, 'ts': ts, 'bot_id': bot_id}
    if user is not None:
        event['user'] = user
    return event


def make_bot(lctx):
    bot = leaguebot.LeagueBot.__new__(leaguebot.LeagueBot)
    bot.lctx = lctx
    bot.logger = mock.MagicMock()
    return bot


class TrustedReporterIntakeTest(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        db.set_config(league_name, configs.BOT_SLACK_USER_ID, SINGLES_BOT)
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, CHANNEL)
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, STREAMBOT_USER)
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def clean(self, event, lctx=None):
        return command_parser.validate_and_clean_message(lctx or self.lctx, event)

    def test_trusted_bot_passes_and_is_flagged(self):
        result = self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT)))
        self.assertEqual('<@U2> over <@U1> 3-1', result['text'])
        self.assertTrue(result['trusted_reporter'])
        self.assertTrue(command_parser.get_command_object(result).is_trusted_reporter)

    def test_trusted_by_bot_id_or_user_id(self):
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, ' BOTHER , {} '.format(STREAMBOT_BOT_ID))
        lctx = LeagueContext.load_from_db(league_name)
        self.assertIsNotNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), user='UNOTLISTED'), lctx))

    def test_untrusted_bot_still_ignored(self):
        self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), bot_id='BRANDOM', user='URANDOM')))

    def test_unset_or_empty_config_ignores_every_bot(self):
        for value in (None, '', ' , '):
            if value is None:
                lctx = LeagueContext(league_name, {k: v for k, v in self.lctx.configs.items() if k != configs.TRUSTED_REPORTER_IDS})
            else:
                db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, value)
                lctx = LeagueContext.load_from_db(league_name)
            self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT)), lctx), repr(value))

    def test_human_listed_as_trusted_gets_no_bot_powers(self):
        human = {'text': '<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), 'channel': CHANNEL, 'user': STREAMBOT_USER, 'ts': '1'}
        result = self.clean(human)
        self.assertFalse(result.get('trusted_reporter', False))
        self.assertFalse(command_parser.get_command_object(result).is_trusted_reporter)

    def test_own_bot_is_never_trusted(self):
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, SINGLES_BOT)
        lctx = LeagueContext.load_from_db(league_name)
        self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), user=SINGLES_BOT), lctx))

    def test_report_for_other_league_bot_is_ignored(self):
        self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(DOUBLES_BOT))))

    def test_trusted_bot_in_dm_or_other_channel_is_ignored(self):
        self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), channel='Dchannel')))
        self.assertIsNone(self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), channel='other')))

    def test_legacy_bot_message_without_user_uses_bot_id(self):
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, STREAMBOT_BOT_ID)
        lctx = LeagueContext.load_from_db(league_name)
        result = self.clean(bot_event('<@{}> <@U2> over <@U1> 3-1'.format(SINGLES_BOT), user=None), lctx)
        self.assertEqual(STREAMBOT_BOT_ID, result['user'])

    def test_trusted_bot_unknown_command_gets_no_reply(self):
        bot = make_bot(self.lctx)
        with patch.object(slack_util, 'post_message') as post:
            bot.message_received({'event': bot_event('<@{}> hello there'.format(SINGLES_BOT))}, None)
        post.assert_not_called()

    def test_trusted_bot_can_only_report_scores(self):
        bot = make_bot(self.lctx)
        for text in ('help', 'group A', 'leaderboard'):
            with patch.object(slack_util, 'post_message') as post:
                bot.message_received({'event': bot_event('<@{}> {}'.format(SINGLES_BOT, text))}, None)
            post.assert_not_called()

    def test_human_unknown_command_still_gets_reply(self):
        bot = make_bot(self.lctx)
        event = {'text': '<@{}> hello there'.format(SINGLES_BOT), 'channel': CHANNEL, 'user': 'uHuman', 'ts': '1'}
        with patch.object(slack_util, 'post_message') as post:
            bot.message_received({'event': event}, None)
        post.assert_called_once()


class SinglesBotReportTest(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        db.set_config(league_name, configs.BOT_SLACK_USER_ID, SINGLES_BOT)
        db.set_config(league_name, configs.COMPETITION_CHANNEL_SLACK_ID, CHANNEL)
        db.set_config(league_name, configs.COMMISSIONER_SLACK_ID, 'commish')
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, STREAMBOT_USER)
        for i in range(1, 5):
            db.add_player(league_name, 'playerA{}'.format(i), 'Player A{}'.format(i), 'A')
        match_making.create_matches_for_season(league_name, datetime.date(2022, 1, 3), 3, [], True)
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def match(self, a, b):
        season = db.get_current_season(league_name)
        return [m for m in db.get_matches_for_season(league_name, season) if {m.player_1_id, m.player_2_id} == {a, b}][0]

    def test_streambot_report_records_end_to_end(self):
        # The exact text hudl/ssb-streaming posts: "<@bot> <@winner> over <@loser> 3-1"
        bot = make_bot(self.lctx)
        with patch.object(slack_util, 'post_message') as post, patch.object(slack_util, 'add_reaction') as react:
            bot.message_received({'event': bot_event('<@{}> <@playerA2> over <@playerA1> 3-1'.format(SINGLES_BOT), ts='42')}, None)
        m = self.match('playerA1', 'playerA2')
        self.assertEqual('playerA2', m.winner_id)
        self.assertEqual({3, 1}, {m.player_1_score, m.player_2_score})
        react.assert_called_once_with(self.lctx, CHANNEL, '42', enter_score.WORKED_REACTION)
        self.assertEqual(CHANNEL, post.call_args[0][2])  # group standings posted in the channel
        bot.logger.info.assert_called()

    def test_handles_message_rules(self):
        def handles(text, trusted=True, user=STREAMBOT_USER, channel=CHANNEL):
            return enter_score.handles_message(self.lctx, CommandMessage(text, channel, user, 'ts', is_trusted_reporter=trusted))
        self.assertTrue(handles('<@playerA2> over <@playerA1> 3-1'))
        self.assertFalse(handles('<@playerA2> over <@playerA1> 3-1', trusted=False))  # a human still needs "me"
        self.assertFalse(handles('me over <@playerA1> 3-1'))  # a bot has no "me"
        self.assertFalse(handles('<@playerA1> over me 3-1'))
        self.assertFalse(handles('<@playerA2> over <@playerA1> 3-1', channel='other'))

    def test_bad_reports_get_the_normal_replies(self):
        for text, expected in [
            ('<@playerA2> over <@playerA1> 3-3', enter_score.get_format_message(self.lctx)),
            ('<@playerA1> over <@playerA1> 3-1', enter_score.PLAYED_YOURSELF_MSG),
            ('<@playerA1> over <@nobody> 3-1', enter_score.NO_MATCH_MSG),
        ]:
            with patch.object(slack_util, 'post_message') as post, patch.object(slack_util, 'add_reaction'):
                enter_score.handle_message(self.lctx, CommandMessage(text, CHANNEL, STREAMBOT_USER, 'ts', is_trusted_reporter=True))
            post.assert_called_once_with(self.lctx, expected, CHANNEL)
        self.assertIsNone(self.match('playerA1', 'playerA2').winner_id)


class DoublesBotReportTest(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], datetime.date(2022, 1, 3), 'A', 1, 3)
        db.set_config(league_name, configs.BOT_SLACK_USER_ID, DOUBLES_BOT)
        db.set_config(league_name, configs.TRUSTED_REPORTER_IDS, STREAMBOT_USER)
        self.lctx = LeagueContext.load_from_db(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def match_ab_cd(self):
        return db.get_match_by_participants(league_name, self.t['AB'], self.t['CD'])

    def send(self, text):
        bot = make_bot(self.lctx)
        with patch.object(slack_util, 'post_message') as post, patch.object(slack_util, 'add_reaction') as react:
            bot.message_received({'event': bot_event('<@{}> {}'.format(DOUBLES_BOT, text))}, None)
        return post, react

    def test_streambot_report_records_team_match(self):
        # One player of each team, as hudl/ssb-streaming posts it
        post, react = self.send('<@uD> over <@uA> 3-2')
        m = self.match_ab_cd()
        self.assertEqual((self.t['CD'], 2, 3), (m.winner_id, m.player_1_score, m.player_2_score))
        react.assert_called_once_with(self.lctx, CHANNEL, '1', enter_score.WORKED_REACTION)

    def test_doubles_rejections_still_fire(self):
        for text, expected in [
            ('<@uA> over <@uB> 3-1', enter_score.SAME_TEAM_MSG.format('uA', 'uB')),
            ('<@uA> <@uC> over <@uD> 3-1', enter_score.SPLIT_SIDE_MSG.format('uA', 'uC')),
            ('<@uZ> over <@uA> 3-1', enter_score.NOT_ON_TEAM_MSG.format('uZ')),
        ]:
            post, _ = self.send(text)
            post.assert_called_once_with(self.lctx, expected, CHANNEL)
        self.assertIsNone(self.match_ab_cd().winner_id)
