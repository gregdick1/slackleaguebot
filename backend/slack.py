import datetime
import time

from slackclient import SlackClient

from backend import db
from backend.bot_config import BotConfig
from backend.league_context import LeagueContext


class LeagueSlackClient:
    def __init__(self, league_name):
        self.lctx = LeagueContext(league_name)
        self.bot_config = BotConfig(league_name)
        self.slack_client = SlackClient(self.bot_config.slack_api_key)

    def get_players_dictionary(self):
        players = db.get_players(self.lctx)
        players_dictionary = dict()
        for player in players:
            players_dictionary[player.slack_id] = player.name
        return players_dictionary

    def send_match_message(self, message, to_user, against_user, players_dictionary, debug=True):
        if to_user is None:
            return

        if against_user is None:
            message = 'This week, you have a bye. Relax and get some practice in.'
        else:
            message = message.replace("@against_user", '<@' + against_user + '>')

        if debug and to_user == self.bot_config.commissioner_slack_id:
            self.slack_client.api_call("chat.postMessage", channel=self.bot_config.commissioner_slack_id, text=message, as_user=True)

        debug_message = message.replace(against_user, players_dictionary[against_user])
        if debug:
            return "Debug sent to " + players_dictionary[to_user] + ": " + debug_message

        if not debug:
            self.slack_client.api_call("chat.postMessage", channel=to_user, text=message, as_user=True)
            return "For reals sent to " + players_dictionary[to_user] + ": " + debug_message

    def send_match_messages(self, message, debug=True):
        today = datetime.datetime.today()
        last_monday = (today - datetime.timedelta(days=today.weekday())).date()

        matches = db.get_matches_for_week(self.lctx, last_monday)
        players_dictionary = self.get_players_dictionary()

        sent_messages = ""
        for match in matches:
            if match.winner_id is None:
                sent_messages = sent_messages + self.send_match_message(message, match.player_1_id, match.player_2_id, players_dictionary, debug=debug) + "\n"
                time.sleep(1.5)

                sent_messages = sent_messages + self.send_match_message(message, match.player_2_id, match.player_1_id, players_dictionary, debug=debug) + "\n"
                time.sleep(1.5)

        return sent_messages

    def send_custom_messages(self, message, debug=True):
        players = db.get_active_players(self.lctx)

        if debug:
            self.slack_client.api_call("chat.postMessage", channel=self.bot_config.commissioner_slack_id, text=message, as_user=True)

        sent_messages = ""
        for player in players:
            if debug:
                sent_messages = sent_messages + "Debug sent to " + player.name + ": " + message + "\n"
            else:
                self.slack_client.api_call("chat.postMessage", channel=player.slack_id, text=message, as_user=True)
                sent_messages = sent_messages + "For reals sent to " + player.name + ": " + message + "\n"

            time.sleep(1.5)

        return sent_messages

    # Currently unused..
    def send_custom_for_missed_games(self, message, num_missed, week, debug=True):
        season = db.get_current_season(self.lctx)
        season_matches = db.get_matches_for_season(self.lctx, season)
        players = {}
        for match in season_matches:
            if match.week <= week and match.winner_id is None:
                if match.player_1_id not in players:
                    players[match.player_1_id] = set()
                if match.player_2_id not in players:
                    players[match.player_2_id] = set()

                players[match.player_1_id].add(match.week)
                players[match.player_2_id].add(match.week)

        for player_id in players:
            test = len(players[player_id])
            if len(players[player_id]) >= num_missed:
                if debug and not player_id == self.bot_config.commissioner_slack_id:
                    print('Sending to', player_id, ':', message)
                else:
                    # slack_client.chat.post_message(player_id, message, as_user=True)
                    print('For reals sent to', player_id, ':', message)
                time.sleep(1.5)
