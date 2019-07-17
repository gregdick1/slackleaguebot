import db
import operator
import datetime
import random
import tie_breaker


def rotate(list):
    return list[1:] + list[:1]

def remove_byes(start_date, matchups):
    """
    Removes byes from a round robin schedule. This effectively shortens the season by two weeks
    by taking the last two weeks of matches and filling them in the rest of the season in place
    of bye matches. This means each player will have one week where they are assigned two matches
    :param matchups: the matches for the group
    :return: the new list of matches
    """
    weeks = sorted(list(set([m['week'] for m in matchups])))
    byes = [m for m in matchups if (m['week'] in weeks[:-2] and (m['player_1'] is None or m['player_2'] is None))]
    if len(byes) == 0:
        return matchups #There are no byes

    last_two_week_matchups = [m for m in matchups if m['week'] in weeks[-2:] and (m['player_1'] is not None and m['player_2'] is not None)]
    for matchup in byes:
        actual_player = matchup['player_1'] or matchup['player_2'] #none coalesce
        filler_match = [m for m in last_two_week_matchups if m['player_1'] == actual_player or m['player_2'] == actual_player][0]
        filler_match['week'] = matchup['week']
        last_two_week_matchups.remove(filler_match)

    #Should always be one remaining filler match...whoever had byes in the last two weeks. Move that game to the first week
    if len(last_two_week_matchups) != 1:
        raise StandardError('Error removing byes.')
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

#This method will add a player to a gruop. It assumes a few things:
#1) The season does not include byes
#2) The group currently has an even number of players
#This will effectively create two new matches for the person being added for the first week, and then one additional
#match for the player the remaining weeks to simulate an odd number group season.
def add_player_to_group(player_name, season_num):
    player = db.get_player_by_name(player_name)
    group_players = [p for p in db.get_active_players() if p.grouping == player.grouping and p.name != player_name]
    dates = [m.week for m in db.get_matches_for_season(season_num)]
    dates = sorted(list(set(dates)))
    first = True
    for week in dates:
        if first:
            db.add_match(player, group_players.pop(0), week, player.grouping, season_num)
            first = False
        db.add_match(player, group_players.pop(0), week, player.grouping, season_num)


def create_matches_for_season(start_date, skip_weeks=[], include_byes=False):
    all_players = db.get_active_players()

    groupings = list(set(map(lambda player:player.grouping, all_players)))
    groupings.sort()

    all_matches = []
    for grouping in groupings:
        group_players = [p for p in all_players if p.grouping == grouping]
        random.shuffle(group_players)
        group_matches = create_matches(start_date, group_players, skip_weeks, include_byes)
        for match in group_matches:
            match['grouping'] = grouping
        all_matches.extend(group_matches)
    season = db.get_current_season()
    season += 1
    for match in all_matches:
        db.add_match(match['player_1'], match['player_2'], match['week'], match['grouping'], season)
        a=0

def get_player_name(players, id):
    for player in players:
        if player.slack_id == id:
            return player.name
    return 'Bye'

def get_player_print(players, id, match):
    for player in players:
        if player.slack_id == id:
            if match.winner_id == id:
                return player.name + ' - 2'
            elif match.winner_id is not None:
                return player.name + ' - ' + str(match.sets - 2)
            else:
                return player.name
    return 'Bye'


def gather_scores(group_matches):
    player_scores = {}
    for match in group_matches:
        if match.winner_id is None:
            continue
        if match.player_1_id not in player_scores:
            player_scores[match.player_1_id] = [0,0,0,0] #matches won/lost, sets won/lost
        if match.player_2_id not in player_scores:
            player_scores[match.player_2_id] = [0,0,0,0]
        if match.player_1_id == match.winner_id:
            player_scores[match.player_1_id][0] += 1
            player_scores[match.player_2_id][1] += 1
            player_scores[match.player_1_id][2] += 2
            player_scores[match.player_2_id][3] += 2
            if match.sets > 2:
                player_scores[match.player_2_id][2] += match.sets - 2
                player_scores[match.player_1_id][3] += match.sets - 2
        else:
            player_scores[match.player_2_id][0] += 1
            player_scores[match.player_1_id][1] += 1
            player_scores[match.player_2_id][2] += 2
            player_scores[match.player_1_id][3] += 2
            if match.sets > 2:
                player_scores[match.player_1_id][2] += match.sets - 2
                player_scores[match.player_2_id][3] += match.sets - 2
    players = [{'player_id':k, 'm_w':v[0], 'm_l':v[1], 's_w':v[2], 's_l':v[3]} for k,v in player_scores.items()]
    players = sorted(players, key=lambda k: (-k['m_w'], k['m_l'], -k['s_w'], k['s_l']))

    return tie_breaker.order_players(players, group_matches)

def print_season_markup(season = None):
    if season is None:
        season = db.get_current_season()
    all_matches = db.get_matches_for_season(season)
    all_players = db.get_players()
    groupings = list(set(map(lambda match:match.grouping, all_matches)))
    weeks = list(set(map(lambda match:match.week, all_matches)))
    groupings.sort()
    weeks.sort()
    output = ''
    ###
    ###||heading 1||heading 2||heading 3||
    ###|cell A1|cell A2|cell A3|
    ###|cell B1|cell B2|cell B3|
    max_group_size = 0
    for grouping in groupings:
        group_players = [p for p in all_players if p.grouping == grouping]
        if len(group_players) > max_group_size:
            max_group_size = len(group_players)

    standing_groups = []
    # standing_groups.append(groupings)
    standing_groups.append(groupings[:6])
    standing_groups.append(groupings[6:])
    first_group = True

    for standing_group in standing_groups:
        if first_group:
            first_group = False
            output += 'h2. Standings\n'
        else:
            output += 'h2. Standings Cont.\n'
        for grouping in standing_group:
            output += '||Group ' + grouping
        output += '||\n'
        for i in range(0, max_group_size):
            output += '|'

            for grouping in standing_group:
                group_matches = [m for m in all_matches if m.grouping == grouping]
                players = gather_scores(group_matches)
                if len(players) > i:
                    p = players[i]
                    output += get_player_name(all_players, p['player_id']) + ' ' + str(p['m_w']) + '-' + str(p['m_l'])# + ' (' + str(p['s_w']) + '-' + str(p['s_l']) + ')'
                else:
                    output += ' '
                output += '|'
            output += '\n'

    for grouping in groupings:
        group_matches = [m for m in all_matches if m.grouping == grouping]
        output += '\nh2. Group '+grouping+'\n'
        matches_by_week = {}
        for week in weeks:
            output += '||'+str(week)
            matches_by_week[week] = [m for m in group_matches if m.week == week]
        output += '||\n'

        for i in range(0, len(matches_by_week[weeks[0]])):
            for week in weeks:
                if i >= len(matches_by_week[week]):
                    break
                m = matches_by_week[week][i]
                output += '|'+get_player_print(all_players, m.player_1_id, m)+'\\\\'+get_player_print(all_players, m.player_2_id, m)
            output+= '|\n'
    
    return output