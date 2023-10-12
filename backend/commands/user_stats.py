from backend import slack_util, db, configs


def handles_message(lctx, command_object):
    if lctx.configs[configs.ENABLE_COMMAND_USER_STATS] == 'FALSE':
        return False

    if command_object.text.upper() == 'MY TOTAL STATS' and command_object.is_dm():
        return True
    return False


def handle_message(lctx, command_object):
    all_matches = db.get_matches(lctx.league_name)
    message = build_stat_message(all_matches, command_object.user)
    slack_util.post_message(lctx, message, command_object.channel)


def build_stat_message(all_matches, user_id):
    my_matches = [x for x in all_matches if (x.player_1_id == user_id or x.player_2_id == user_id) and x.winner_id is not None]
    total_won_matches = 0
    total_lost_matches = 0
    total_won_sets = 0
    total_lost_sets = 0
    for match in my_matches:
        if user_id == match.winner_id:
            total_won_matches += 1
            total_won_sets += match.sets_needed
            total_lost_sets += match.sets - match.sets_needed
        else:
            total_lost_matches += 1
            total_lost_sets += match.sets_needed
            total_won_sets += match.sets - match.sets_needed

    message = f"\n Matches Won: {total_won_matches} | Matches Lost: {total_lost_matches} | Sets Won: {total_won_sets} | Sets Lost: {total_lost_sets}"
    return message
