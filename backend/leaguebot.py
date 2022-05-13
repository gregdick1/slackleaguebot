import logging
import time
from multiprocessing import Process

from slackclient import SlackClient
from websocket import WebSocketConnectionClosedException

from backend import command_parser, configs, slack_util
from backend.league_context import LeagueContext


class LeagueBot:
    def __init__(self, league_name):
        self.lctx = LeagueContext.load_from_db(league_name)
        self.lctx.slack_client = SlackClient(self.lctx.configs[configs.SLACK_API_KEY])

        self.logger = logging.getLogger(league_name)

        hdlr = logging.FileHandler(self.lctx.configs[configs.LOG_PATH])
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

        self.logger.debug('booting up leaguebot file')

    def keepalive(self):
        while True:
            time.sleep(3)
            try:
                self.lctx.slack_client.server.ping()
            except WebSocketConnectionClosedException as e:
                self.logger.debug('Keep alive web socket exception.')
                self.lctx.slack_client.rtm_connect()

    def start_bot(self):
        p = Process(target=self.keepalive)
        p.start()

        if self.lctx.slack_client.rtm_connect():
            print("LeagueBot connected and running!")

            while True:
                try:
                    message_list = self.lctx.slack_client.rtm_read()
                    message_list = command_parser.filter_invalid_messages(self.lctx, message_list)

                    for message in message_list:
                        try:
                            command = command_parser.determine_command(self.lctx, message)
                            if command is not None:
                                command.handle_message(self.lctx, message)
                            else:
                                slack_util.post_message(self.lctx, "I don't recognize that. Try `help` to see what I can do.", message['channel'])
                        except Exception as e:
                            self.logger.debug(e)
                            slack_util.add_reaction(self.lctx, message["channel"], message["ts"], "x")

                    time.sleep(1)
                except Exception as e:
                    self.logger.debug('Main while loop web socket exception.', e)
                    self.lctx.slack_client.rtm_connect()
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

