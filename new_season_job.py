import db, slack, match_making, players
import datetime

#match_making.create_matches_for_season(datetime.date(2019, 6, 22), skip_weeks=[], include_byes=False)
match_making.create_matches_for_season(datetime.date(2019, 6, 3), skip_weeks=[], include_byes=False)
# players.ensure_players_in_db()
# players.update_groupings()
# match_making.add_player_to_group('Daniel Shaefer', 10)
# match_making.add_player_to_group('Drew Henning', 10)
# db.clear_matches_for_season(11)
# players.update_groupings()
#
# db.clear_matches_for_season(2)
print match_making.print_season_markup()
# db.push_db()