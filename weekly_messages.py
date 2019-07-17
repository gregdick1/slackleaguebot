import db
import match_making
import players
import slack

import datetime


# PULL DOWN THE DB FIRST!
# slack.send_custom_to_active('When you have a moment, please fill out this short survey for some potential changes to season 2. https://hudlresearch.typeform.com/to/bM2DK7', debug=False)
# slack.send_custom_to_active('When you have a moment, please fill out this short survey about Season 3. https://hudlresearch.typeform.com/to/nULo4x', debug=False)
# slack.send_custom_to_active('Season 6 starts May 15 (as long as current matches get finished up). You will automatically be included. If you do *not* wish to participate, please let <@> know asap.', debug=False)

four_game_message = "You currently have 3 unplayed matches. Friendly warning that if you don't play a match this week, you'll be booted from this season on monday."
three_game_message = "Season ends Feb 1 and you currently have 3 or more unplayed matches. This is your friendly warning that you are at risk of being removed for next season. If you need to appeal for leniency, dm <@U04QW49D1>."
new_season_message = "The next season starts July 22nd. By receiving this message, you will be entered automatically. If you don't want to participate, please let <@U04QW49D1> know asap if you haven't already."
rankings_updated_message = "Standings for season 3 have been updated. Please finish remaining matches before July 12th. You can view them here: https://sync.hudlnet.com/pages/viewpage.action?pageId=135990683"

debug = False
# slack.send_custom_for_missed_games(four_game_message, 3, datetime.date(2019,3,4), debug=debug)
slack.send_custom_to_active(new_season_message, debug=debug)

# Monday Message
# yyyy m d
# slack.send_messages_for_week(datetime.date(2019,5,29), debug=debug)
# slack.send_messages_for_week(datetime.date(2019,6,24), debug=debug)

# Thursday Messages (reminders, then rankings updated)
# yyyy m d
#slack.send_reminders_for_week(datetime.date(2019,7,1), debug=debug)
#print(match_making.print_season_markup())
#slack.send_custom_to_active(rankings_updated_message, debug=debug)

# db.rm_db()

