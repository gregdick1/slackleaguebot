import os
import paramiko


def get_ssh_client(context):
    ssh_client = paramiko.SSHClient()
    # don't like this auto add policy, but may be needed for nondev commissioners
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.load_system_host_keys()
    # make these configurable, and maybe a password
    ssh_client.connect(context.server_host, context.server_port, context.server_user)
    return ssh_client


def can_connect_to_server(context):
    ssh_client = get_ssh_client(context)
    stdin, stdout, stderror = ssh_client.exec_command('ls')
    stdin.close()  # necessary quirk
    return len(stdout) > 0


def is_bot_running(context, ssh_client=None):
    bot_ids = _get_running_bot_ids(context, ssh_client)
    # should always be 2
    return len(bot_ids) == 2


def _get_running_bot_ids(context, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    stdin, stdout, stderror = local_ssh_client.exec_command('ps -ef | grep "{} {}"'.format(context.bot_command, context.bot_name))
    stdin.close()  # necessary quirk
    tmp = stdout.readlines()
    running_bot_ids = []
    for line in tmp:
        parts = line.split(' ')
        parts = [x for x in parts if len(x) > 0]
        if len(parts) >= 9 and parts[7] == context.bot_command and parts[8] == '{}\n'.format(context.bot_name):
            running_bot_ids.append(parts[1])
    if ssh_client is None:
        local_ssh_client.close()
    return running_bot_ids


def stop_bot(context):
    ssh_client = get_ssh_client(context)
    ids_to_kill = _get_running_bot_ids(context, ssh_client)
    if len(ids_to_kill) == 2:
        kill_command = 'kill {}; kill {}'.format(ids_to_kill[0], ids_to_kill[1])
        stdin, stdout, stderror = ssh_client.exec_command(kill_command)
        stdin.close()  # necessary quirk

    success = not is_bot_running(context, ssh_client)
    ssh_client.close()
    return success


def start_bot(context):
    ssh_client = get_ssh_client(context)
    if is_bot_running(context, ssh_client):
        ssh_client.close()
        return True

    channel = ssh_client.get_transport().open_session()
    channel.exec_command('cd {}/; nohup {} {} &'.format(context.league_folder, context.bot_command, context.bot_name))
    channel.close()

    success = is_bot_running(context, ssh_client)
    ssh_client.close()
    return success


def create_folder_on_server(context, folder, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    _folder_exists(context, folder, local_ssh_client)
    stdin, stdout, stderror = local_ssh_client.exec_command('mkdir {}'.format(folder))
    stdin.close()  # necessary quirk
    success = _folder_exists(context, folder, local_ssh_client)
    if ssh_client is None:
        local_ssh_client.close()
    return success


def _folder_exists(context, folder_including_league_folder, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    stdin, stdout, stderror = local_ssh_client.exec_command('ls {}'.format(folder_including_league_folder))
    stdin.close()  # necessary quirk
    tmp = stderror.readlines()
    # can't read stdin because an empty folder will have no output. So read stderror and check for no errors
    exists = len(tmp) == 0
    if ssh_client is None:
        local_ssh_client.close()
    return exists


def file_exists(context, local_path_from_project_root, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    stdin, stdout, stderror = local_ssh_client.exec_command('ls {}/{}'.format(context.league_folder, local_path_from_project_root))
    stdin.close()  # necessary quirk
    tmp = stdout.readlines()
    exists = context.league_folder+'/'+local_path_from_project_root+'\n' in tmp
    if ssh_client is None:
        local_ssh_client.close()
    return exists


def upload_file(context, local_path_from_project_root, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    sftp = local_ssh_client.open_sftp()
    # ../ needed assuming this file is one folder deep from project root
    sftp.put('../{}'.format(local_path_from_project_root), '{}/{}'.format(context.league_folder, local_path_from_project_root))
    sftp.close()
    if ssh_client is None:
        local_ssh_client.close()


def _download_file(context, local_path_from_project_root):
    ssh_client = get_ssh_client(context)
    sftp = ssh_client.open_sftp()
    # ../ needed assuming this file is one folder deep from project root
    sftp.get('{}/{}'.format(context.league_folder, local_path_from_project_root), '../{}'.format(local_path_from_project_root))
    sftp.close()
    ssh_client.close()


#TODO set up cron job for match and reminder messages
def _get_cron_list(context, ssh_client=None):
    local_ssh_client = ssh_client if ssh_client is not None else get_ssh_client(context)
    stdin, stdout, stderror = local_ssh_client.exec_command('crontab -l')
    stdin.close()  # necessary quirk
    tmp = stdout.readlines()

    if ssh_client is None:
        local_ssh_client.close()
    return False




# test_league_folder = 'compbottest'
# local_path = 'public/index.html'
# _upload_file(local_path, test_league_folder)
# _download_file('public/test.html', test_league_folder)
#

# command = 'python'
# bot_name = 'bot.py'
# league_folder = 'pongbot'
#
# started = start_bot(command, bot_name, league_folder)
# print('Started bot: {}'.format(started))
#
# stopped = stop_bot(command, bot_name)
# print('Stopped bot: {}'.format(stopped))


# create ssh client
# ssh_client = _get_ssh_client()

# sftp = ssh_client.open_sftp()
# sftp.get('pongbot/hudl_pong_league.sqlite', 'hudl_pong_league.sqlite')
# sftp.close()
# ssh_client.close()
