import logging

from slack_sdk import WebClient
from slack_bolt import App, BoltContext
from slack_bolt.adapter.socket_mode import SocketModeHandler

from backend import command_parser, configs, slack_util
from backend.league_context import LeagueContext


class LeagueBot:
    def __init__(self, league_name):
        self.lctx = LeagueContext.load_from_db(league_name)
        self.lctx.slack_client = WebClient(token=self.lctx.configs[configs.SLACK_API_KEY])

        self.logger = logging.getLogger(league_name)

        hdlr = logging.FileHandler(self.lctx.configs[configs.LOG_PATH])
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

        self.logger.debug('booting up leaguebot file')

    def app_home_opened(self):
        pass

    def app_home_opened_lazy(self):
        pass

    def message_received(self, body, logger):
        message = command_parser.validate_and_clean_message(self.lctx, body['event'])
        try:
            command = command_parser.determine_command(self.lctx, message)
            if command is not None:
                command.handle_message(self.lctx, command_parser.get_command_object(message))
            else:
                slack_util.post_message(self.lctx, "I don't recognize that. Try `help` to see what I can do.", message['channel'])
        except Exception as e:
            self.logger.debug(e)
            slack_util.add_reaction(self.lctx, message["channel"], message["ts"], "x")

    def message_received_lazy(self, event, context: BoltContext, client: WebClient):
        pass

    def start_bot(self):
        app = App(token=self.lctx.configs[configs.SLACK_API_KEY])
        app.event('app_home_opened')(ack=self.app_home_opened, lazy=[self.app_home_opened_lazy])
        app.event('app_mention')(ack=self.message_received, lazy=[self.message_received_lazy])
        app.event('message')(ack=self.message_received, lazy=[self.message_received_lazy])
        SocketModeHandler(app, self.lctx.configs[configs.SLACK_APP_KEY]).start()

