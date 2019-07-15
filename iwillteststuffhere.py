from slackclient import SlackClient
import bot_config

slack_client = SlackClient(bot_config.get_slack_api_key())
response = slack_client.api_call('channels.history', channel=bot_config.get_channel_slack_id(), count=20)

for message in response['messages']:
    print message

