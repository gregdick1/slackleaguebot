import db
from league_context import LeagueContext

KEY_SLACK_API_KEY = 'SLACK_API_KEY'
KEY_BOT_SLACK_USER_ID = 'BOT_SLACK_USER_ID'
KEY_COMPETITION_CHANNEL_SLACK_ID = 'COMPETITION_CHANNEL_SLACK_ID'
KEY_COMMISSIONER_SLACK_ID = 'COMMISSIONER_SLACK_ID'
KEY_LOG_PATH = 'LOG_PATH'

LEAGUE_CONFIGS = [KEY_SLACK_API_KEY, KEY_BOT_SLACK_USER_ID, KEY_COMPETITION_CHANNEL_SLACK_ID, KEY_COMMISSIONER_SLACK_ID,
                  KEY_LOG_PATH]


class BotConfig:
    def __init__(self, league_name):
        lctx = LeagueContext(league_name)
        self.league_context = lctx
        self.slack_api_key = db.get_config(lctx, KEY_SLACK_API_KEY)
        self.bot_slack_user_id = db.get_config(lctx, KEY_BOT_SLACK_USER_ID)
        self.channel_slack_id = db.get_config(lctx, KEY_COMPETITION_CHANNEL_SLACK_ID)
        self.commissioner_slack_id = db.get_config(lctx, KEY_COMMISSIONER_SLACK_ID)
        self.log_path = db.get_config(lctx, KEY_LOG_PATH)

    def get_all_configs(self):
        configs = {}
        # TODO this can be optimized to a single db query or just grab the ones on the object
        for config_key in LEAGUE_CONFIGS:
            configs[config_key] = db.get_config(self.league_context, config_key)
        return configs
