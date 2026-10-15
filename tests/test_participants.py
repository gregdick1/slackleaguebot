import datetime
from unittest import TestCase

import test_league_setup
import doubles_fixture
from backend import db, configs, participants
from backend.league_context import LeagueContext

league_name = 'unittest'


class TestSingles(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        db.add_player(league_name, 'p1', 'Player One', 'A')
        db.add_player(league_name, 'p2', 'Player Two', 'B')
        db.set_active(league_name, 'p2', False)
        self.r = participants.resolver(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_singles_lookups(self):
        r = self.r
        self.assertFalse(r.doubles)
        self.assertFalse(participants.is_doubles(LeagueContext.load_from_db(league_name)))
        self.assertEqual('Player One', r.display_name('p1'))
        self.assertEqual('Bye', r.display_name(None))
        self.assertEqual('Bye', r.display_name('nobody'))
        self.assertEqual(['p1'], r.slack_ids('p1'))
        self.assertEqual([], r.slack_ids(None))
        self.assertEqual('<@p1>', r.tag('p1'))
        self.assertEqual({'p1': 'Player One', 'p2': 'Player Two'}, r.names_map())
        self.assertEqual('p1', r.participant_for_user('p1', 1))
        self.assertIsNone(r.participant_for_user('nobody', 1))
        self.assertIsNone(r.partner_of('p1', 1))
        self.assertEqual('B', r.grouping_of('p2'))
        self.assertEqual(['p1'], r.participants_for_season(1))
        matches = db.get_matches(league_name)
        self.assertIs(matches, r.player_view(matches, 'p1'))

    def test_set_league_format(self):
        participants.set_league_format(league_name, 'DOUBLES')
        self.assertEqual('DOUBLES', db.get_config(league_name, configs.LEAGUE_FORMAT))
        self.assertEqual(participants.DOUBLES_MATCH_MESSAGE, db.get_config(league_name, configs.MATCH_MESSAGE))
        participants.set_league_format(league_name, 'SINGLES')
        self.assertEqual(db.DEFAULT_MATCH_MESSAGE, db.get_config(league_name, configs.MATCH_MESSAGE))
        db.set_config(league_name, configs.MATCH_MESSAGE, 'custom')
        participants.set_league_format(league_name, 'DOUBLES')
        self.assertEqual('custom', db.get_config(league_name, configs.MATCH_MESSAGE))  # custom text is never overwritten

    def test_set_league_format_rejects_bad_values_and_locks(self):
        for bad in ['doubles', 'TRIOS', '', None]:
            with self.assertRaises(ValueError):
                participants.set_league_format(league_name, bad)
        db.add_match_by_ids(league_name, 'p1', None, datetime.date(2022, 1, 3), 'A', 1, 3)
        with self.assertRaises(ValueError) as ctx:
            participants.set_league_format(league_name, 'DOUBLES')
        self.assertEqual('League format cannot change after matches exist.', str(ctx.exception))
        self.assertEqual('SINGLES', db.get_config(league_name, configs.LEAGUE_FORMAT))


class TestDoubles(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.t = doubles_fixture.make_doubles_league(season_matches=False)
        self.next_team = db.add_team(league_name, 2, 'uZ', 'uA', 'A')
        db.add_match_by_ids(league_name, self.t['AB'], self.t['CD'], datetime.date(2022, 1, 3), 'A', 1, 3)
        db.update_match_by_participants(league_name, self.t['CD'], self.t['AB'], 3, 1, 0)
        self.r = participants.resolver(league_name)

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def test_doubles_lookups(self):
        r, t = self.r, self.t
        self.assertTrue(r.doubles)
        self.assertEqual('Bob-omb Squad (Alice & Bob)', r.display_name(t['AB']))
        self.assertEqual('Carol & Dan', r.display_name(t['CD']))
        self.assertEqual('Bye', r.display_name(None))
        self.assertEqual(['uA', 'uB'], r.slack_ids(t['AB']))
        self.assertEqual('Bob-omb Squad (<@uA> & <@uB>)', r.tag(t['AB']))
        self.assertEqual('<@uC> & <@uD>', r.tag(t['CD']))
        self.assertEqual('Carol & Dan', r.names_map()[t['CD']])
        self.assertEqual(t['AB'], r.participant_for_user('uB', 1))
        self.assertEqual(self.next_team, r.participant_for_user('uA', 2))
        self.assertIsNone(r.participant_for_user('uZ', 1))  # only on next season's draft team
        self.assertEqual('uB', r.partner_of('uA', 1))
        self.assertIsNone(r.partner_of('uZ', 1))
        self.assertEqual('B', r.grouping_of(t['GH']))
        self.assertEqual([t['AB'], t['CD'], t['EF'], t['GH']], r.participants_for_season(1))

    def test_player_view_rewrites_team_ids_to_user(self):
        view = self.r.player_view(db.get_matches(league_name), 'uB')
        self.assertEqual(1, len(view))
        self.assertEqual(('uB', self.t['CD'], self.t['CD']), (view[0].player_1_id, view[0].player_2_id, view[0].winner_id))
        original = db.get_matches(league_name)[0]
        self.assertEqual(self.t['AB'], original.player_1_id)  # DB rows untouched
