import sftp
import os
import sqlite3
from admin_context import Context

server_folders = ['backend']


def create_league_folders(context):
    ssh_client = sftp.get_ssh_client(context)
    sftp.create_folder_on_server(context, context.league_folder)
    for folder in server_folders:
        sftp.create_folder_on_server(context, context.league_folder + '/' + folder)
    ssh_client.close()


def move_files_to_server(context):
    ssh_client = sftp.get_ssh_client(context)
    for folder in server_folders:
        for item in os.listdir('../'+folder):
            if os.path.isfile('../'+folder+'/'+item):
                sftp.upload_file(context, folder + '/' + item, ssh_client)
    ssh_client.close()


def create_and_deploy_start_bot_file(context):
    if sftp.file_exists(context, context.bot_name):
        return True

    f = open('../'+context.bot_name, "w")
    f.write("""from backend.leaguebot import LeagueBot

if __name__ == "__main__":
    LeagueBot({}).start_bot()
""".format(context.league_name))
    f.close()

    sftp.upload_file(context, context.bot_name)
    os.remove('../'+context.bot_name)


def create_and_deploy_bot_db(context):
    # Connecting to the database file
    db_path = "../{}_league.sqlite".format(context.league_name)
    # path = os.path.abspath(os.path.join(os.path.dirname(__file__), db_path))

    sftp.upload_file(context, context.league_name + '_league.sqlite')

    # remove the db from local because we always want to grab fresh from the server
    os.remove(db_path)


def create_league(context):
    create_league_folders(context)
    create_and_deploy_start_bot_file(context)
    create_and_deploy_bot_db(context)
    move_files_to_server(context)
    #TODO set up cron job for reminder messages

