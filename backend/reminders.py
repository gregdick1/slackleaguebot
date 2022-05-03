import time, datetime
import db, bot_config
import slackclient
from bot_config import BotConfig
from league_context import LeagueContext

slack_client = slackclient.SlackClient(bot_config.get_slack_api_key())


class LeagueSlackClient:
    def __init__(self, league_name):
        self.lctx = LeagueContext(league_name)
        self.bot_config = BotConfig(league_name)

    def get_players_dictionary(self):
        players = db.get_players(self.lctx)
        players_dictionary = dict()
        for player in players:
            players_dictionary[player.slack_id] = player.name
        return players_dictionary


def run():
    today = datetime.datetime.today()

    matches = db.get_matches()
    todays_matches = [x for x in matches if x.week == today]
    players_dictionary = get_players_dictionary()

    sent_messages = ""
    for match in matches:
        if match.winner_id is None:
            sent_messages = sent_messages + send_match_message(message, match.player_1_id, match.player_2_id, players_dictionary, debug=debug) + "\n"
            time.sleep(1.5)

            sent_messages = sent_messages + send_match_message(message, match.player_2_id, match.player_1_id, players_dictionary, debug=debug) + "\n"
            time.sleep(1.5)

    return sent_messages

def send_match_message(message, to_user, against_user, players_dictionary, debug=True):
    if to_user is None:
        return

    if against_user is None:
        message = 'This week, you have a bye. Relax and get some practice in.'
    else:
        message = message.replace("@against_user", '<@' + against_user + '>')

    if debug and to_user == bot_config.get_commissioner_slack_id():
        response = slack_client.api_call('chat.postMessage', channel=bot_config.get_commissioner_slack_id(), as_user=True, text=message)

    debug_message = message.replace(against_user, players_dictionary[against_user])
    if debug:
        return "Debug sent to " + players_dictionary[to_user] + ": " + debug_message

    if not debug:
        response = slack_client.api_call('chat.postMessage', channel=to_user, as_user=True, text=message)
        slack_client.chat.post_message(to_user, message, as_user=True)
        return "For reals sent to " + players_dictionary[to_user] + ": " + debug_message


if __name__ == "__main__":
    run()
