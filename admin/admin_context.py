from admin import admin_config


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

    @classmethod
    def load_from_db(cls, league_name):
        configs = admin_config.get_leagues()
        return Context(league_name,
                       configs[admin_config.BOT_COMMAND],
                       configs[admin_config.SERVER_HOST],
                       configs[admin_config.SERVER_PORT],
                       configs[admin_config.SERVER_USER])
