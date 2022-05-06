from datetime import datetime

from admin import sftp, admin_config


def download_db(context):
    sftp.download_file(context, context.db_name)
    # Update admin config for the time
    admin_config.set_config(context.league_name, admin_config.LAST_DOWNLOADED, datetime.now())
