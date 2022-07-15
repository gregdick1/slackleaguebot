import os
from datetime import datetime

from admin import sftp, admin_config, db_management
from admin.admin_context import Context
from backend import db

server_folders = ['backend', 'backend/commands', 'backend/scenario_analysis']
root_path = os.path.join(os.path.dirname(__file__), '..')


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
    LeagueBot('{}').start_bot()
""".format(context.league_name))
    f.close()

    sftp.upload_file(context, context.bot_name)
    os.remove(os.path.join(root_path, context.bot_name))


def _create_and_deploy_run_reminders_file(context):
    filename = 'run_reminders.py'
    if sftp.file_exists(context, filename):
        return True

    f = open(os.path.join(root_path, filename), "w")
    f.write("""from backend import reminders

if __name__ == "__main__":
    reminders.run_reminders('{}', debug=False)
""".format(context.league_name))
    f.close()

    sftp.upload_file(context, filename)
    os.remove(os.path.join(root_path, filename))


def _create_and_deploy_bot_db(context):
    db.initialize(context.league_name)
    sftp.upload_file(context, context.db_name)


def deploy_code(league_name):
    context = Context.load_from_db(league_name)
    if sftp.folder_exists(context, 'backend'):
        sftp.delete_folder_on_server(context, 'backend')
    _create_league_folders(context)
    _move_files_to_server(context)
    return "Deploy Successful"


def deploy_league(league_name):
    context = Context.load_from_db(league_name)
    if sftp.file_exists(context, context.db_name):
        db_management.download_db(context)
        return "Connected to Existing"

    _create_league_folders(context)
    _create_and_deploy_start_bot_file(context)
    _create_and_deploy_run_reminders_file(context)
    _move_files_to_server(context)
    _create_and_deploy_bot_db(context)
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())
    return "Deploy Successful"
    #TODO set up cron job for reminder messages

