import os

from admin import sftp
from admin.admin_context import Context
from backend import db, league_context

server_folders = ['backend']
root_path = os.path.join( os.path.dirname( __file__ ), '..' )

def _create_league_folders(context):
    ssh_client = sftp.get_ssh_client(context)
    sftp.create_folder_on_server(context, context.league_folder)
    for folder in server_folders:
        sftp.create_folder_on_server(context, context.league_folder + '/' + folder)
    ssh_client.close()


def _move_files_to_server(context):
    ssh_client = sftp.get_ssh_client(context)
    for folder in server_folders:
        for item in os.listdir(os.path.join(root_path, folder)):
            if os.path.isfile(os.path.join(root_path, folder, item)):
                sftp.upload_file(context, folder + '/' + item, ssh_client)
    ssh_client.close()


def _create_and_deploy_start_bot_file(context):
    if sftp.file_exists(context, context.bot_name):
        return True

    f = open(os.path.join(root_path, context.bot_name), "w")
    f.write("""from backend.leaguebot import LeagueBot

if __name__ == "__main__":
    LeagueBot({}).start_bot()
""".format(context.league_name))
    f.close()

    sftp.upload_file(context, context.bot_name)
    os.remove(os.path.join(root_path, context.bot_name))


def _create_and_deploy_bot_db(context, lctx):
    db.initialize(lctx)
    sftp.upload_file(context, context.league_name + '_league.sqlite')


def deploy_league(league_name):
    context = Context.load_from_db(league_name)
    if sftp.file_exists(context, context.league_name + '_league.sqlite'):
        return "Connected to Existing"

    lctx = league_context.LeagueContext(league_name)
    _create_league_folders(context)
    _create_and_deploy_start_bot_file(context)
    _move_files_to_server(context)
    _create_and_deploy_bot_db(context, lctx)
    return "Deploy Successful"
    #TODO set up cron job for reminder messages

