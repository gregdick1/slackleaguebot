from backend import tie_breaker, db, configs


def get_player_print(players, id, match):
    for player in players:
        if player.slack_id == id:
            if match.winner_id == id:
                return player.name + ' - 3'
            elif match.winner_id is not None:
                return player.name + ' - ' + str(match.sets - 3)
            else:
                return player.name
    return 'Bye'


def get_player_name(players, id):
    for player in players:
        if player.slack_id == id:
            return player.name
    return 'Bye'


def gather_scores(group_matches):
    player_scores = {}
    for match in group_matches:
        if match.player_1_id not in player_scores:
            player_scores[match.player_1_id] = [0, 0, 0, 0, 0]  # matches won/lost, sets won/lost/tied
        if match.player_2_id not in player_scores:
            player_scores[match.player_2_id] = [0, 0, 0, 0, 0]
        if match.winner_id is None:
            continue
        if match.player_1_id == match.winner_id:
            player_scores[match.player_1_id][0] += 1
            player_scores[match.player_2_id][1] += 1
        else:
            player_scores[match.player_2_id][0] += 1
            player_scores[match.player_1_id][1] += 1
        player_scores[match.player_1_id][2] += match.player_1_score
        player_scores[match.player_1_id][3] += match.player_2_score
        player_scores[match.player_1_id][4] += match.tie_score
        player_scores[match.player_2_id][2] += match.player_2_score
        player_scores[match.player_2_id][3] += match.player_1_score
        player_scores[match.player_2_id][4] += match.tie_score

    players = [{'player_id': k, 'm_w': v[0], 'm_l': v[1], 's_w': v[2], 's_l': v[3], 's_t': v[4]} for k, v in player_scores.items()]
    players = sorted(players, key=lambda k: (-k['m_w'], k['m_l'], -k['s_w'], k['s_l'], k['s_t']))

    return tie_breaker.order_players(players, group_matches)


def print_season_markup(lctx, season=None):
    if season is None:
        season = db.get_current_season(lctx.league_name)
    all_matches = db.get_matches_for_season(lctx.league_name, season)
    all_players = db.get_players(lctx.league_name)
    groupings = list(set(map(lambda match: match.grouping, all_matches)))
    weeks = list(set(map(lambda match: match.week, all_matches)))
    groupings.sort()
    weeks.sort()
    output = ''
    ###
    # ||heading 1||heading 2||heading 3||
    # |cell A1|cell A2|cell A3|
    # |cell B1|cell B2|cell B3|
    max_group_size = 0
    for grouping in groupings:
        group_players = [p for p in all_players if p.grouping == grouping]
        if len(group_players) > max_group_size:
            max_group_size = len(group_players)

    groups_per_row = 4
    standing_groups = [groupings[:groups_per_row], groupings[groups_per_row:]]
    # standing_groups.append(groupings)
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
                players = [x for x in players if x['player_id'] is not None]
                if len(players) > i:
                    p = players[i]
                    output += get_player_name(all_players, p['player_id']) + ' ' + str(p['m_w']) + '-' + str(
                        p['m_l'])  # + ' (' + str(p['s_w']) + '-' + str(p['s_l']) + ')'
                else:
                    output += ' '
                output += '|'
            output += '\n'

    for grouping in groupings:
        group_matches = [m for m in all_matches if m.grouping == grouping]
        output += '\nh2. Group ' + grouping + '\n'
        matches_by_week = {}
        for week in weeks:
            output += '||' + str(week)
            matches_by_week[week] = [m for m in group_matches if m.week == week]
        output += '||\n'

        for i in range(0, len(matches_by_week[weeks[0]])):
            for week in weeks:
                if i >= len(matches_by_week[week]):
                    break
                m = matches_by_week[week][i]
                output += '|' + get_player_print(all_players, m.player_1_id, m) + '\\\\' + get_player_print(all_players,
                                                                                                            m.player_2_id,
                                                                                                            m)
            output += '|\n'

    return output


def get_players_dictionary(lctx):
    players = db.get_players(lctx.league_name)
    players_dictionary = dict()
    for player in players:
        players_dictionary[player.slack_id] = player.name
    return players_dictionary


def replace_message_variables(lctx, message):
    message = message.replace('@bot_name', '<@{}>'.format(lctx.configs[configs.BOT_SLACK_USER_ID]))
    message = message.replace('#competition_channel',
                              '<#{}>'.format(lctx.configs[configs.COMPETITION_CHANNEL_SLACK_ID]))
    return message


def get_players_record(lctx, p1_id, p2_id):
    rivary_matches = db.get_matches_between_players(lctx.league_name, p1_id, p2_id)
    p1_wins = 0
    p2_wins = 0
    if len(rivary_matches) == 0:
        return {'p1_wins': 0, 'p2_wins': 0}

    for m in rivary_matches:
        if m.winner_id == p1_id:
            p1_wins += 1
        elif m.winner_id == p2_id:
            p2_wins += 1
    return {'p1_wins': p1_wins, 'p2_wins': p2_wins}

