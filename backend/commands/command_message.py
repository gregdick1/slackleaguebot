class CommandMessage:
    def __init__(self, text, channel, user, timestamp):
        self.text = text
        self.channel = channel
        self.user = user
        self.timestamp = timestamp

    def is_dm(self):
        return self.channel.startswith('D')
