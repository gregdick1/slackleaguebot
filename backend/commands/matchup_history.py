from backend import slack_util, configs, db, utility


def handles_message(lctx, command_object):
    if lctx.configs[configs.ENABLE_COMMAND_MATCHUP_HISTORY] == 'FALSE':
        return False

    if command_object.text.upper().startswith('MATCHUP HISTORY') and command_object.is_dm():
        return True
    return False


def handle_message(lctx, command_object):
    show_all = command_object.text.upper().endswith('ALL')
    all_players = db.get_players(lctx.league_name)
    matches_by_opponent = get_matches_by_opponent(lctx.league_name, command_object.user)
    match_summaries = [build_matchup_summary(matches_by_opponent[x], command_object.user, x) for x in matches_by_opponent]
    match_summaries.sort(key=lambda x: (x['matches'], x['wins']), reverse=True)

    active_player_ids = [x.slack_id for x in db.get_active_players(lctx.league_name)]
    full_print = '*Opponent: Matches (Sets) | Wins & Losses in order*'
    for ms in match_summaries:
        if not show_all and ms['opponent_id'] not in active_player_ids:
            continue
        full_print += '\n'+get_summary_print(ms, all_players)
    slack_util.post_message(lctx, full_print, command_object.channel)


def get_matches_by_opponent(league_name, player_id):
    matches = db.get_matches(league_name)
    player_matches = [x for x in matches if x.winner_id is not None and not x.forfeit and (x.player_1_id == player_id or x.player_2_id == player_id)]
    matches_by_opponent = {}
    for match in player_matches:
        opponent_id = [x for x in [match.player_1_id, match.player_2_id] if x != player_id][0]
        if opponent_id not in matches_by_opponent:
            matches_by_opponent[opponent_id] = []
        matches_by_opponent[opponent_id].append(match)
    return matches_by_opponent


def build_matchup_summary(matches, player_id, opponent_id):
    matches.sort(key=lambda x: x.week)
    summary = {
        'opponent_id': opponent_id,
        'matches': len(matches),
        'wins': len([x for x in matches if x.winner_id == player_id]),
        'sets': sum([x.sets for x in matches]),
        'set_wins': sum([max(x.player_1_score, x.player_2_score) for x in matches if x.winner_id == player_id]) + sum([min(x.player_1_score, x.player_2_score) for x in matches if x.winner_id != player_id])
    }
    summary['losses'] = summary['matches'] - summary['wins']
    summary['set_losses'] = summary['sets'] - summary['set_wins']

    win_lose_string = ''
    for match in matches:
        if match.winner_id == player_id:
            win_lose_string += 'W '
        else:
            win_lose_string += 'L '
    summary['win_lose_string'] = win_lose_string

    return summary


def get_summary_print(summary, all_players):
    opponent_name = utility.get_player_name(all_players, summary['opponent_id'])
    to_print = opponent_name + ': {}-{} ({}-{})'.format(summary['wins'], summary['losses'], summary['set_wins'], summary['set_losses'])
    to_print += ' | ' + summary['win_lose_string']
    return to_print
