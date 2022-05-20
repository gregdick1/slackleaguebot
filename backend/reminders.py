import datetime

from slackclient import SlackClient

from backend import configs, slack_util, utility, db
from backend.league_context import LeagueContext


def run_reminders(league_name):
    debug = True  # Keep true until we verify this works
    lctx = LeagueContext.load_from_db(league_name)

    today = datetime.date.today()
    reminder_days = db.get_reminder_days_since(league_name, today)
    if {'date': today, 'sent': 0} not in reminder_days:
        return

    lctx.slack_client = SlackClient(lctx.configs[configs.SLACK_API_KEY])
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    new_match_message = utility.replace_message_variables(lctx, lctx.configs[configs.MATCH_MESSAGE])
    reminder_message = utility.replace_message_variables(lctx, lctx.configs[configs.REMINDER_MESSAGE])

    sent_match_ids = slack_util.send_match_messages(lctx, new_match_message, today, False, [], debug=debug)
    sent_reminder_ids = slack_util.send_match_messages(lctx, reminder_message, yesterday, True, sent_match_ids, debug=debug)
    slack_util.post_message(lctx,
                            'Cron Job Reminders Sent: {} Match Messages, {} Reminder Messages'.format(len(sent_match_ids), len(sent_reminder_ids)),
                            lctx.configs[configs.COMMISSIONER_SLACK_ID])
    if not debug:
        db.mark_reminder_day_sent(league_name, today)
