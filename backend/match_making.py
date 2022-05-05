import datetime
import random

from backend import db


def remove_byes(start_date, matchups):
    """
    Removes byes from a round robin schedule. This effectively shortens the season by two weeks
    by taking the last two weeks of matches and filling them in the rest of the season in place
    of bye matches. This means each player will have one week where they are assigned two matches
    :param start_date: the first date of the matchups
    :param matchups: the matches for the group
    :return: the new list of matches
    """
    weeks = sorted(list(set([m['week'] for m in matchups])))
    byes = [m for m in matchups if (m['week'] in weeks[:-2] and (m['player_1'] is None or m['player_2'] is None))]
    if len(byes) == 0:
        return matchups  # There are no byes

    last_two_week_matchups = [m for m in matchups if m['week'] in weeks[-2:] and (m['player_1'] is not None and m['player_2'] is not None)]
    for matchup in byes:
        actual_player = matchup['player_1'] or matchup['player_2']  # none coalesce
        filler_match = [m for m in last_two_week_matchups if m['player_1'] == actual_player or m['player_2'] == actual_player][0]
        filler_match['week'] = matchup['week']
        last_two_week_matchups.remove(filler_match)

    # Should always be one remaining filler match...whoever had byes in the last two weeks. Move that game to the first week
    if len(last_two_week_matchups) != 1:
        raise Exception('Error removing byes.')
    last_two_week_matchups[0]['week'] = start_date

    return [m for m in matchups if (m['week'] in weeks[:-2] and (m['player_1'] is not None and m['player_2'] is not None))]


def create_matches(start_date, players, skip_weeks, include_byes=False):
    """ Generates a schedule of "fair" pairings from a list of units """
    if len(players) % 2:
        players.append(None)
    matchups = []
    week_dates = []
    week = 0
    for week_idx in range(0, len(players)-1):
        week_date = start_date + datetime.timedelta(weeks=week)
        while week_date in skip_weeks:
            week += 1
            week_date = start_date + datetime.timedelta(weeks=week)
        week_dates.append(week_date)
        week += 1

    for week_date in week_dates:
        for i in range(int(len(players)/2)):
            matchups.append({
                'player_1': players[i],
                'player_2': players[-i-1],
                'week': week_date
            })
        players.insert(1, players.pop())
    if include_byes:
        return matchups
    return remove_byes(start_date, matchups)


# This method will add a player to a group. It assumes a few things:
# 1) The season does not include byes
# 2) The group currently has an even number of players
# This will effectively create two new matches for the person being added for the first week, and then one additional
# match for the player the remaining weeks to simulate an odd number group season.
def add_player_to_group(lctx, player_name, season_num):
    player = db.get_player_by_name(lctx, player_name)
    group_players = [p for p in db.get_active_players(lctx) if p.grouping == player.grouping and p.name != player_name]
    dates = [m.week for m in db.get_matches_for_season(lctx, season_num)]
    dates = sorted(list(set(dates)))
    first = True
    for week in dates:
        # TODO use config for sets needed
        if first:
            db.add_match(lctx, player, group_players.pop(0), week, player.grouping, season_num, 3)
            first = False
        db.add_match(lctx, player, group_players.pop(0), week, player.grouping, season_num, 3)


def create_matches_for_season(lctx, start_date, sets_needed, skip_weeks=None, include_byes=False):
    if skip_weeks is None:
        skip_weeks = []
    all_players = db.get_active_players(lctx)

    groupings = list(set(map(lambda player: player.grouping, all_players)))
    groupings.sort()

    all_matches = []
    for grouping in groupings:
        group_players = [p for p in all_players if p.grouping == grouping]
        random.shuffle(group_players)
        group_matches = create_matches(start_date, group_players, skip_weeks, include_byes)
        for match in group_matches:
            match['grouping'] = grouping
        all_matches.extend(group_matches)
    season = db.get_current_season(lctx)
    season += 1
    for match in all_matches:
        db.add_match(lctx, match['player_1'], match['player_2'], match['week'], match['grouping'], season, sets_needed)
