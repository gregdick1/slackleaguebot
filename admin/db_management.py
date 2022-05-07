import os
from datetime import datetime

from admin import sftp, admin_config
from backend import db, league_context

root_path = os.path.join(os.path.dirname(__file__), '..')


def download_db(context):
    sftp.download_file(context, context.db_name)
    # Update admin config for the time
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())
    db.clear_commands_to_run(league_context.LeagueContext(context.league_name))


def _upload_db(context):
    ssh_client = sftp.get_ssh_client(context)
    _cycle_db_backups(context, ssh_client)
    sftp.upload_file(context, context.db_name, ssh_client)
    ssh_client.close()


def _cycle_db_backups(context, ssh_client):
    db_path = context.db_name  # path on server is simply root folder and db name
    sftp.delete_file_on_server(context, db_path + '.bak4', ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak3', db_path + '.bak4', ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak2', db_path + '.bak3', ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak1', db_path + '.bak2', ssh_client)
    sftp.rename_file_on_server(context, db_path, db_path + '.bak1', ssh_client)


def _uncycle_db_backups(context):
    db_path = context.db_name  # path on server is simply root folder and db name
    ssh_client = sftp.get_ssh_client(context)
    sftp.delete_file_on_server(context, db_path, ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak1', db_path, ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak2', db_path + '.bak1', ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak3', db_path + '.bak2', ssh_client)
    sftp.rename_file_on_server(context, db_path + '.bak4', db_path + '.bak3', ssh_client)


def undo_commit(context):
    _uncycle_db_backups(context)
    download_db(context)


def commit_commands(context):
    # local backup of db
    db_path = os.path.join(root_path, context.db_name)
    os.rename(db_path, db_path+'.bak')
    sftp.download_file(context, context.db_name)

    lctx = league_context.LeagueContext(context.league_name)

    try:
        conn = db.get_connection(lctx)
        c = conn.cursor()
        for command in db.get_commands_to_run(lctx):
            c.execute(command)
        conn.commit()
        conn.close()
    except Exception as e:
        print('Error executing commands on copy of server db. Canceling that process and restoring local db.')
        print(e)
        os.remove(db_path)
        os.rename(db_path+'.bak', db_path)
        return "There was an error applying the updates to the db. The process was rolled back. The db on the server is unchanged."

    _upload_db(context)
    os.remove(db_path+'.bak')
    db.clear_commands_to_run(lctx)
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())
