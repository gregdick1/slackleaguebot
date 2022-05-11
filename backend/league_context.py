from backend import db

KEY_SLACK_API_KEY = 'SLACK_API_KEY'
KEY_BOT_SLACK_USER_ID = 'BOT_SLACK_USER_ID'
KEY_COMPETITION_CHANNEL_SLACK_ID = 'COMPETITION_CHANNEL_SLACK_ID'
KEY_COMMISSIONER_SLACK_ID = 'COMMISSIONER_SLACK_ID'
KEY_LOG_PATH = 'LOG_PATH'

LEAGUE_VERSION = 'LEAGUE_VERSION'

LEAGUE_CONFIGS = [KEY_SLACK_API_KEY, KEY_BOT_SLACK_USER_ID, KEY_COMPETITION_CHANNEL_SLACK_ID, KEY_COMMISSIONER_SLACK_ID,
                  KEY_LOG_PATH]


# Useful context to be passed around to all the other league backend files
class LeagueContext:
    def __init__(self, league_name, configs, slack_client=None):
        self.league_name = league_name
        self.slack_client = slack_client
        self.configs = configs

    @classmethod
    def load_from_db(cls, league_name, slack_client=None):
        configs = {
            KEY_SLACK_API_KEY: db.get_config(league_name, KEY_SLACK_API_KEY),
            KEY_BOT_SLACK_USER_ID: db.get_config(league_name, KEY_BOT_SLACK_USER_ID),
            KEY_COMMISSIONER_SLACK_ID: db.get_config(league_name, KEY_COMMISSIONER_SLACK_ID),
            KEY_COMPETITION_CHANNEL_SLACK_ID: db.get_config(league_name, KEY_COMPETITION_CHANNEL_SLACK_ID),
            KEY_LOG_PATH: db.get_config(league_name, KEY_LOG_PATH)
        }
        return LeagueContext(league_name, configs, slack_client)