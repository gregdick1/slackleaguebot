class CommandMessage:
    def __init__(self, text, channel, user, timestamp, is_trusted_reporter=False):
        self.text = text
        self.channel = channel
        self.user = user
        self.timestamp = timestamp
        # A bot from TRUSTED_REPORTER_IDS, allowed to report a score for two other players
        self.is_trusted_reporter = is_trusted_reporter

    def is_dm(self):
        return self.channel.startswith('D')
