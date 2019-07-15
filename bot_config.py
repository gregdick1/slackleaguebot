import json
import os
# For first time setup, copy default_config.py to config.py and replace placeholder fields

text_config={}
if os.path.isfile('config.json'):
    with open('config.json') as data_file:
        text_config = json.load(data_file)

def _get_value_for_key(key):
    if key in os.environ:
        return os.environ[key]
    return text_config[key]

def get_slack_api_key():
    return _get_value_for_key('SLACK_API_KEY')

def get_bot_slack_user_id():
    return _get_value_for_key('BOT_SLACK_USER_ID')

def get_channel_slack_id():
    return _get_value_for_key('PONG_CHANNEL_SLACK_ID')

def get_commissioner_slack_id():
    return _get_value_for_key('COMMISSIONER_SLACK_ID')

def get_log_path():
    return _get_value_for_key('LOG_PATH')