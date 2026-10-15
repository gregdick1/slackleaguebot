import datetime
from unittest import TestCase

from flask import Flask

import test_league_setup
import doubles_fixture
from app_routes import league_config_tab, playerboard_tab, matches_tab
from backend import db, configs

league_name = 'unittest'


def make_client():
    app = Flask(__name__)
    app.register_blueprint(league_config_tab.league_config_api)
    app.register_blueprint(playerboard_tab.playerboard_api)
    app.register_blueprint(matches_tab.matches_api)
    return app.test_client()


class Test(TestCase):
    def setUp(self):
        test_league_setup.teardown_test_league()
        test_league_setup.create_test_league()
        self.client = make_client()

    def tearDown(self):
        test_league_setup.teardown_test_league()

    def set_format(self, value):
        return self.client.post('/set-league-config', json={'selectedLeague': league_name, 'configKey': 'LEAGUE_FORMAT', 'configValue': value}).get_json()

    def test_format_lock(self):
        self.assertEqual({'hasMatches': False}, self.client.get('/get-league-has-matches', query_string={'leagueName': league_name}).get_json())
        self.assertEqual({'success': True}, self.set_format('DOUBLES'))
        self.assertIn('@partner_user', db.get_config(league_name, configs.MATCH_MESSAGE))
        self.assertFalse(self.set_format('doubles')['success'])
        db.add_match_by_ids(league_name, 'x', None, datetime.date(2022, 1, 3), 'A', 1, 3)
        self.assertEqual({'hasMatches': True}, self.client.get('/get-league-has-matches', query_string={'leagueName': league_name}).get_json())
        self.assertEqual({'success': False, 'message': 'League format cannot change after matches exist.'}, self.set_format('SINGLES'))
        self.assertEqual('DOUBLES', db.get_config(league_name, configs.LEAGUE_FORMAT))
        other = self.client.post('/set-league-config', json={'selectedLeague': league_name, 'configKey': 'BOT_NAME', 'configValue': '@x'})
        self.assertEqual(b'Success', other.data)

    def test_format_lock_invalid_values(self):
        # lowercase 'doubles' and 'TRIOS' must be rejected; stored value must be unchanged
        initial = db.get_config(league_name, configs.LEAGUE_FORMAT)
        r1 = self.set_format('doubles')
        self.assertFalse(r1['success'])
        self.assertEqual(initial, db.get_config(league_name, configs.LEAGUE_FORMAT))
        r2 = self.set_format('TRIOS')
        self.assertFalse(r2['success'])
        self.assertEqual(initial, db.get_config(league_name, configs.LEAGUE_FORMAT))

    def test_team_routes_and_season(self):
        doubles_fixture.make_doubles_league(season_matches=False)
        db.clear_matches_for_season(league_name, 1)
        conn = db.get_connection(league_name)
        conn.execute('DELETE FROM team')
        conn.commit()
        conn.close()

        post = lambda url, body: self.client.post(url, json=dict(body, leagueName=league_name)).get_json()
        r1 = post('/add-team', {'member1': 'uA', 'member2': 'uB', 'grouping': 'A', 'name': 'Squad'})
        r2 = post('/add-team', {'member1': 'uC', 'member2': 'uD', 'grouping': 'A', 'name': ''})
        self.assertEqual(('T1-1', 'T1-2'), (r1['teamId'], r2['teamId']))
        self.assertEqual({'success': False, 'message': 'Alice is already on a team for season 1.'},
                         post('/add-team', {'member1': 'uA', 'member2': 'uZ', 'grouping': 'A', 'name': ''}))
        self.assertTrue(post('/update-team', {'teamId': 'T1-2', 'name': 'Duo'})['success'])
        self.assertTrue(post('/update-team-grouping-and-orders', {'teamIds': ['T1-2', 'T1-1'], 'grouping': 'A'})['success'])

        drafts = self.client.get('/get-draft-teams', query_string={'leagueName': league_name}).get_json()
        self.assertEqual(1, drafts['season'])
        self.assertEqual(['Duo (Carol & Dan)', 'Squad (Alice & Bob)'], [t['display_name'] for t in drafts['teams']])

        first = post('/create-season', {'startDate': '2022-01-03T00:00:00.000Z', 'skipWeeks': [], 'setsNeeded': 3, 'playAllSets': False, 'includeByes': False})
        self.assertEqual({'success': True}, first)
        names = self.client.get('/get-participant-names', query_string={'leagueName': league_name}).get_json()
        self.assertEqual('Squad (Alice & Bob)', names['T1-1'])
        self.assertFalse(post('/delete-team', {'teamId': 'T1-1'})['success'])
        again = post('/create-season', {'startDate': '2022-03-07T00:00:00.000Z', 'skipWeeks': [], 'setsNeeded': 3, 'playAllSets': False, 'includeByes': False})
        self.assertEqual({'success': False, 'message': 'No teams for next season. Add teams on the Playerboard first.'}, again)

    def test_ranked_players_with_team_ids(self):
        doubles_fixture.make_doubles_league()
        rows = self.client.get('/get-players-from-season', query_string={'leagueName': league_name, 'season': 1}).get_json()
        self.assertIn('Bob-omb Squad (Alice & Bob)', [r['name'] for r in rows])
        self.assertTrue(all(r['id'].startswith('T1-') for r in rows))

    def test_create_season_bad_start_date(self):
        doubles_fixture.make_doubles_league(season_matches=False)
        db.clear_matches_for_season(league_name, 1)
        conn = db.get_connection(league_name)
        conn.execute('DELETE FROM team')
        conn.commit()
        conn.close()
        post = lambda url, body: self.client.post(url, json=dict(body, leagueName=league_name)).get_json()
        post('/add-team', {'member1': 'uA', 'member2': 'uB', 'grouping': 'A', 'name': 'Squad'})
        post('/add-team', {'member1': 'uC', 'member2': 'uD', 'grouping': 'A', 'name': ''})
        # bad startDate should return success:False with a message, not raise a 500
        result = post('/create-season', {'startDate': 'not-a-date', 'skipWeeks': [], 'setsNeeded': 3, 'playAllSets': False, 'includeByes': False})
        self.assertFalse(result['success'])
        self.assertIn('message', result)
