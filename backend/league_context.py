import os
from backend import db


# Useful context to be passed around to all the other league backend files
class LeagueContext:
    def __init__(self, league_name, loaded_configs, slack_client=None):
        self.league_name = league_name
        self.slack_client = slack_client
        self.configs = loaded_configs

    @classmethod
    def load_from_db(cls, league_name, slack_client=None):
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "configs.py"))
        config_keys = []
        with open(config_path) as f:
            for line in f:
                key, value = line.split('=')
                value = value.replace('\'', '').replace('\n', '').strip()
                config_keys.append(value)

        loaded_configs = {}
        for k in config_keys:
            loaded_configs[k] = db.get_config(league_name, k)

        return LeagueContext(league_name, loaded_configs, slack_client)
