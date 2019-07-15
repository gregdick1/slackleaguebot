from slackclient import SlackClient
import bot_config
import db
from match_making import gather_scores, get_player_name
import time
from websocket import WebSocketConnectionClosedException
from multiprocessing import Process

import logging, sys

class SmashBot():
    def __init__(self):
        self.slack_client = SlackClient(bot_config.get_slack_api_key())
        self.logger = logging.getLogger('smashbot')

        hdlr = logging.FileHandler(bot_config.get_log_path())
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.DEBUG)

        self.logger.debug('booting up smashbot file')

    def keepalive(self):
        while True:
            time.sleep(3)
            try:
                self.slack_client.server.ping()
            except WebSocketConnectionClosedException as e:
                self.logger.debug('Keep alive web socket exception.')
                self.slack_client.rtm_connect()

    def format_name(self, player, last_initial = False):
        first = player['first_name']
        last = player['last_name'].strip()
        if last_initial:
            return (first + ' ' + last[:1]).strip()
        try:
            last = last[:last.index(' ')]
        finally:
            return (first + ' ' + last).strip()

    def print_help(self, channel):
        message = 'I support the following:'
        message = message + '\n`@sul help` - see these commands'
        message = message + '\n`@sul me over @them 2-2` or `@sul @them over me 2-1` - report a score'
        message = message + '\n`@sul group a [with sets]` - see the current rankings of a group, optionally include sets'
        self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)

    def print_group(self, channel, group):
        try:
            include_sets = False

            if group.endswith(' with sets'):
                include_sets = True
                group = group[:group.index(' with sets')].strip()

            season = db.get_current_season()
            all_matches = db.get_matches_for_season(season)
            all_players = db.get_players()
            group_matches = [m for m in all_matches if m.grouping.lower() == group]
            if not len(group_matches):
                raise Exception('Not a match')
            players = gather_scores(group_matches)
            message = 'Group ' + group.upper() + ':'
            for p in players:
                message += '\n' + get_player_name(all_players, p['player_id']) + ' ' + str(p['m_w']) + '-' + str(p['m_l'])
                if include_sets:
                    message += ' ('+str(p['s_w'])+'-'+str(p['s_l'])+')'
            self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
        except Exception as e:
            self.logger.debug(e)
            self.slack_client.api_call("chat.postMessage", channel=channel, text="Not a group (or I messed up).", as_user=True)

    def parse_score(self, command, poster, admin=False):
        try:
            if admin and command.startswith('<@'):
                winner = command[command.index('<@') + 2:command.index('>')].upper()
                temp = command[command.index('>') + 1:]
                loser = temp[temp.index('<@') + 2:temp.index('>')].upper()
                score = temp[temp.index('>') + 1:].strip()
            elif command.startswith('me over '):
                winner = poster
                loser = command[command.index('<@')+2:command.index('>')].upper()
                score = command[command.index('>') + 1:].strip()
            elif command.startswith('<@') and command.index('over me') > 0:
                loser = poster
                winner = command[command.index('<@')+2:command.index('>')].upper()
                score = command[command.index('me') + 2:].strip()

            else:
                raise Exception('Bad format')

            scores = score.split('-')
            if(len(scores) > 2):
                raise Exception('Malformed score')
            score_1 = int(scores[0].strip())
            if score_1 != 2:
                raise Exception('Malformed score')
            score_2 = int(scores[1].strip())
            score_total = score_1 + score_2
            if not (2 <= score_total <= 3):
                raise Exception('Malformed score')

            return {
                'winner_id': winner,
                'loser_id': loser,
                'score_total': score_total
            }

        except Exception as e:
            self.logger.error(e)
            return None

    def enter_score(self, winner_id, loser_id, score_total, channel, timestamp):
        try:
            if not db.update_match_by_id(winner_id, loser_id, score_total):
                self.slack_client.api_call("chat.postMessage", channel=channel,
                                           text='Not a match I have (or I messed up).', as_user=True)
                return

            self.slack_client.api_call("chat.postMessage", channel=bot_config.get_commissioner_slack_id(),
                                       text='Entered into db', as_user=True)
            self.slack_client.api_call("reactions.add", name="white_check_mark", channel=channel, timestamp=timestamp)

        except:
            self.slack_client.api_call("chat.postMessage", channel=bot_config.get_commissioner_slack_id(),
                                       text='Failed to enter into db', as_user=True)
            e = sys.exc_info()[0]
            self.logger.error(e)

    def handle_command(self, command, channel, poster, timestamp):
        command = command.lower().strip()

        if command == 'help':
            self.print_help(channel)
            return

        if command.startswith('group '):
            self.print_group(channel, command[6:].strip())
            return

        result = self.parse_score(command, poster)
        if result is None:
            format_msg = "Didn't catch that. The format is `@sul me over @them 2-1` or `@sul @them over me 2-1`."
            self.slack_client.api_call("chat.postMessage", channel=channel,
                                       text=format_msg, as_user=True)
            return

        self.enter_score(result['winner_id'], result['loser_id'], result['score_total'], channel, timestamp)

    def handle_direct_message_command(self, command, channel):
        if command.startswith('group '):
            self.print_group(channel, command[6:].strip())

    def handle_admin_direct_message_command(self, command, channel, timestamp):
        if command.startswith('group '):
            self.print_group(channel, command[6:].strip())
            return

        result = self.parse_score(command, None, admin=True)
        if result is None:
            format_msg = "Still here."
            self.slack_client.api_call("chat.postMessage", channel=channel,
                                       text=format_msg, as_user=True)
            return

        self.enter_score(result['winner_id'], result['loser_id'], result['score_total'], channel, timestamp)

    def parse_message(self, output):
        message_text = ""
        message_channel = ""
        user_id = ""
        timestamp = ""
        if output and 'text' in output and 'channel' in output and 'user' in output and 'ts' in output:
            message_text = output['text']
            message_channel = output['channel']
            user_id = output['user']
            timestamp = output['ts']
        else:
            self.logger.error('Invalid message - ' + str(output))
            return

        # Sent in SSB channel
        if message_channel == bot_config.get_channel_slack_id() and message_text.startswith('<@' + bot_config.get_bot_slack_user_id() + '>'):
            self.logger.debug('Got an output that I handle - ' + str(output))
            self.handle_command(message_text[12:].strip(), message_channel, user, timestamp)

        # Normal DM
        elif message_channel[:1] == 'D':
            self.logger.debug('Got an direct message that I handle - ' + str(output))

            if user_id == bot_config.get_commissioner_slack_id():
                self.handle_admin_direct_message_command(message_text.strip(), message_channel, timestamp)
            else:
                self.handle_direct_message_command(message_text.strip(), message_channel)

    def start_bot(self):
        p = Process(target=self.keepalive)
        p.start()

        if self.slack_client.rtm_connect():
            print("StarterBot connected and running!")
            while True:
                try:
                    output_list = self.slack_client.rtm_read()
                    for output in output_list:
                        self.parse_message(output)

                    time.sleep(10)
                except Exception as e:
                    self.logger.debug('Main while loop web socket exception.', e)
                    self.slack_client.rtm_connect()
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

if __name__ == "__main__":
    SmashBot().start_bot()