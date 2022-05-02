
# Useful context to be passed around the all the other admin file
class Context:
    def __init__(self, league_name, bot_command, server_host, server_port, server_user):
        self.league_name = league_name
        self.bot_name = "start_{}_league.py".format(league_name)
        self.league_folder = "{}_league".format(league_name)
        self.bot_command = bot_command
        self.server_host = server_host
        self.server_port = server_port
        self.server_user = server_user
