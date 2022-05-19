import os
from datetime import datetime
from shutil import copyfile

from admin import sftp, admin_config, db_updater
from backend import db

root_path = os.path.join(os.path.dirname(__file__), '..')


def download_db(context):
    sftp.download_file(context, context.db_name)
    # Update admin config for the time
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())
    db.clear_commands_to_run(context.league_name)


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


def _backup_local_and_download(context):
    # local backup of db
    db_path = os.path.join(root_path, context.db_name)
    os.rename(db_path, db_path + '.bak')
    try:
        sftp.download_file(context, context.db_name)
    except Exception as e:
        print('Error connecting to server. Canceling that process and restoring local db.')
        print(e)
        os.rename(db_path + '.bak', db_path)
        raise e


def _commit_commands_to_local(context, commands):
    db_path = os.path.join(root_path, context.db_name)
    if not os.path.exists(db_path + '.bak'):
        message = "Can't commit commands to local. The backup db doesn't exist. Expecting: "+db_path+".bak"
        print(message)
        raise Exception(message)
    try:
        conn = db.get_connection(context.league_name)
        c = conn.cursor()
        for command in commands:
            c.execute(command)
        conn.commit()
        conn.close()
        db.clear_commands_to_run(context.league_name)
    except Exception as e:
        print('Error executing commands on copy of server db. Canceling that process and restoring local db.')
        print(e)
        os.remove(db_path)
        os.rename(db_path+'.bak', db_path)
        raise e


def _update_local_db_version(context):
    db_path = os.path.join(root_path, context.db_name)
    if not os.path.exists(db_path + '.bak'):
        message = "Can't update local db version. The backup db doesn't exist. Expecting: " + db_path + ".bak"
        print(message)
        raise Exception(message)
    try:
        db_updater.run_updates(context.league_name)
    except Exception as e:
        print('Error updating the local db version. Canceling that process and restoring local db.')
        print(e)
        os.remove(db_path)
        os.rename(db_path + '.bak', db_path)
        raise e


def _updload_and_cleanup(context):
    db_path = os.path.join(root_path, context.db_name)
    if not os.path.exists(db_path + '.bak'):
        message = "Can't upload and clean up. The backup db doesn't exist. Expecting: " + db_path + ".bak"
        print(message)
        raise Exception(message)

    _upload_db(context)
    os.remove(db_path+'.bak')
    db.clear_commands_to_run(context.league_name)
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())


def _ensure_no_current_backup(context):
    db_path = os.path.join(root_path, context.db_name)
    if os.path.exists(db_path + '.bak'):
        os.remove(db_path + '.bak')


def perform_update(context):
    _ensure_no_current_backup(context)
    db_path = os.path.join(root_path, context.db_name)

    has_deployed = admin_config.get_config(context.league_name, admin_config.HAS_DEPLOYED) == 'True'
    if has_deployed:
        # Get commands before refreshing db from the server
        commands = db.get_commands_to_run(context.league_name)
        try:
            _backup_local_and_download(context)
        except Exception as e:
            return "There was an error connecting to the server. The process was rolled back. The db on the server is unchanged."

        try:
            _commit_commands_to_local(context, commands)
        except Exception as e:
            return "There was an error applying the updates to the db. The process was rolled back. The db on the server is unchanged."
    else:
        # simple local backup
        copyfile(db_path, db_path + '.bak')

    try:
        _update_local_db_version(context)
    except Exception as e:
        return "There was an error updating the db version. The process was rolled back. The db on the server is unchanged."

    # TODO probably need more error handling here
    if has_deployed:
        _updload_and_cleanup(context)
    else:
        # Simple backup cleanup
        os.remove(db_path + '.bak')
        db.clear_commands_to_run(context.league_name)


def commit_commands(context):
    _ensure_no_current_backup(context)

    # Get commands before refreshing db from the server
    commands = db.get_commands_to_run(context.league_name)
    try:
        _backup_local_and_download(context)
    except Exception as e:
        return "There was an error connecting to the server. The process was rolled back. The db on the server is unchanged."

    try:
        _commit_commands_to_local(context, commands)
    except Exception as e:
        return "There was an error applying the updates to the db. The process was rolled back. The db on the server is unchanged."

    _updload_and_cleanup(context)
