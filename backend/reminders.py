import datetime

from slackclient import SlackClient

from backend import configs, slack_util, utility, db
from backend.league_context import LeagueContext


# dates is iso format strings of datetimes, not date objects
def update_reminders_days(league_name, season, dates):
    date_objs = [datetime.datetime.fromisoformat(x[:-1]).date() for x in dates]  # Remove the Z from the end
    existing = [x['date'] for x in db.get_reminder_days_for_season(league_name, season)]

    # Adding
    new_dates = [x for x in date_objs if x not in existing]
    for new_date in new_dates:
        db.add_reminder_day(league_name, season, new_date)

    # removing one
    to_remove = [x for x in existing if x not in date_objs]
    for date in to_remove:
        db.remove_reminder_day(league_name, season, date)


def run_reminders(league_name, debug=True):
    lctx = LeagueContext.load_from_db(league_name)

    today = datetime.date.today()
    season = db.get_current_season(league_name)
    reminder_days = db.get_reminder_days_since(league_name, season, today)
    if {'date': today, 'sent': 0, 'season': season} not in reminder_days:
        return

    lctx.slack_client = SlackClient(lctx.configs[configs.SLACK_API_KEY])
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    new_match_message = utility.replace_message_variables(lctx, lctx.configs[configs.MATCH_MESSAGE])
    reminder_message = utility.replace_message_variables(lctx, lctx.configs[configs.REMINDER_MESSAGE])

    sent_match_ids = slack_util.send_match_messages(lctx, new_match_message, today, False, [], debug=debug)
    sent_reminder_ids = slack_util.send_match_messages(lctx, reminder_message, yesterday, True, sent_match_ids, debug=debug)
    slack_util.post_message(lctx,
                            'Cron Job Reminders Sent: {} Match Messages, {} Reminder Messages, Debug={}'.format(len(sent_match_ids), len(sent_reminder_ids), debug),
                            lctx.configs[configs.COMMISSIONER_SLACK_ID])
    if not debug:
        db.mark_reminder_day_sent(league_name, season, today)
