import copy
from unittest import TestCase
from backend.scenario_analysis import scenario_utility


class Match:
    def __init__(self, id, p1_id, p2_id, winner_id, play_all_sets, sets):
        self.id = id
        self.player_1_id = p1_id
        self.player_2_id = p2_id
        self.winner_id = winner_id
        self.sets = sets
        self.play_all_sets = play_all_sets
        self.sets_needed = sets


class Test(TestCase):
    def test_is_top_x_wins(self):
        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 2},
            {'player_id': 'd', 'm_w': 1},
        ]
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'e', 2))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'd', 10))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'c', 3))
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'c', 2))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 1))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'd', 4))

        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 1},
            {'player_id': 'e', 'm_w': 1},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'b', 2))
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'c', 2))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'c', 3))

        ordered_players = [
            {'player_id': 'a', 'm_w': 3},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 1},
            {'player_id': 'e', 'm_w': 1},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'a', 1))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'b', 1))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'c', 1))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'a', 2))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'b', 2))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'c', 2))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 3))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'b', 3))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'c', 3))

        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'd', 3))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'd', 4))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'd', 5))

        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 3},
            {'player_id': 'e', 'm_w': 3},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 1))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 2))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 3))

    def test_is_top_x_wins_reverse(self):
        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 2},
            {'player_id': 'd', 'm_w': 1},
        ]
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'e', 2, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 10, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'b', 3, reverse=True))
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'b', 2, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'd', 1, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'a', 4, reverse=True))

        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 2},
            {'player_id': 'e', 'm_w': 2},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'e', 2, reverse=True))
        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'd', 2, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'd', 3, reverse=True))

        ordered_players = [
            {'player_id': 'a', 'm_w': 3},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 1},
            {'player_id': 'e', 'm_w': 1},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'f', 1, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'e', 1, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'd', 1, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'f', 2, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'e', 2, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'd', 2, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'f', 3, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'e', 3, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'd', 3, reverse=True))

        self.assertEqual(2, scenario_utility.is_top_x_wins(ordered_players, 'c', 3, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'c', 4, reverse=True))
        self.assertEqual(1, scenario_utility.is_top_x_wins(ordered_players, 'c', 5, reverse=True))

        ordered_players = [
            {'player_id': 'a', 'm_w': 4},
            {'player_id': 'b', 'm_w': 3},
            {'player_id': 'c', 'm_w': 3},
            {'player_id': 'd', 'm_w': 3},
            {'player_id': 'e', 'm_w': 3},
            {'player_id': 'f', 'm_w': 1},
        ]
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'f', 1, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'f', 2, reverse=True))
        self.assertEqual(0, scenario_utility.is_top_x_wins(ordered_players, 'f', 3, reverse=True))

    def test_scenario_sets_identical(self):
        scenario_a = [
            Match(1, 'a', 'b', 'a', 0, 3),
            Match(2, 'b', 'c', 'b', 0, 3),
            Match(3, 'c', 'd', 'c', 0, 3),
            Match(4, 'd', 'a', 'd', 0, 3),
        ]
        scenario_b = [
            Match(1, 'a', 'b', 'b', 0, 3),
            Match(2, 'b', 'c', 'c', 0, 3),
            Match(3, 'c', 'd', 'd', 0, 5),
            Match(4, 'd', 'a', 'a', 0, 4),
        ]
        scenario_list_1 = [scenario_a[:], scenario_b[:]]
        scenario_b.reverse()
        scenario_list_2 = [scenario_b[:], scenario_a[:]]

        self.assertTrue(scenario_utility.scenario_sets_identical(scenario_list_1, scenario_list_2))
        scenario_list_2 = [scenario_b[:]]
        self.assertFalse(scenario_utility.scenario_sets_identical(scenario_list_1, scenario_list_2))
        self.assertFalse(scenario_utility.scenario_sets_identical(scenario_list_1, []))
        self.assertFalse(scenario_utility.scenario_sets_identical([scenario_a], [scenario_b]))

    def test_reduce_scenarios(self):

        def double_scenarios(scenarios, match):
            list_a = [x[:] for x in scenarios]
            list_b = [x[:] for x in scenarios]
            m_a = copy.copy(match)
            m_b = copy.copy(match)
            m_a.winner_id = m_a.player_1_id
            m_b.winner_id = m_b.player_2_id
            for scenario in list_a:
                scenario.append(m_a)
            for scenario in list_b:
                scenario.append(m_b)
            return list_a+list_b

        theoretical_matches = [
            Match(99, 'z', 'y', 'z', 0, 3),
            Match(1, 'a', 'b', 'a', 0, 3),
            Match(2, 'b', 'c', 'b', 0, 3),
            Match(3, 'c', 'd', 'c', 0, 3),
            Match(4, 'd', 'a', 'd', 0, 3)
        ]
        total_scenarios = [[theoretical_matches[0]]]
        total_scenarios = double_scenarios(total_scenarios, theoretical_matches[1])
        total_scenarios = double_scenarios(total_scenarios, theoretical_matches[2])
        total_scenarios = double_scenarios(total_scenarios, theoretical_matches[3])
        total_scenarios = double_scenarios(total_scenarios, theoretical_matches[4])
        reduced_scenarios = scenario_utility.reduce_scenarios(total_scenarios, theoretical_matches)
        self.assertEqual(1, len(reduced_scenarios))

    def test_build_combo_array(self):
        combo_index = 55
        binary = scenario_utility.build_combo_array(combo_index, 2, 6)
        self.assertEqual([1, 1, 1, 0, 1, 1], binary)  # remember the result is in reverse order of our expected binary number

        binary = scenario_utility.build_combo_array(combo_index, 2, 8)
        self.assertEqual([1, 1, 1, 0, 1, 1, 0, 0], binary)

        trinary = scenario_utility.build_combo_array(combo_index, 3, 6)
        self.assertEqual([1, 0, 0, 2, 0, 0], trinary)

        quadnary = scenario_utility.build_combo_array(combo_index, 4, 4)
        self.assertEqual([3, 1, 3, 0], quadnary)

    def test_create_match_scenario(self):
        unplayed_matches = [
            Match(1, 'a', 'e', None, 0, 3),
            Match(2, 'b', 'f', None, 0, 3),
            Match(3, 'c', 'g', None, 0, 3),
            Match(4, 'd', 'h', None, 0, 3)
        ]
        # Combo index essentially needs to be 0-15 and correspond to a binary combination possible winner outcomes
        # For example, 0000 would be all player 1s as winners. 1111 would be all player 2s
        # Note that it applies to matches in reverse order, so 1010 would result in p1, p2, p1, p2
        matches = scenario_utility.create_match_scenario(unplayed_matches, 0)
        self.assertEqual(['a', 'b', 'c', 'd'], [x.winner_id for x in matches])
        matches = scenario_utility.create_match_scenario(unplayed_matches, 15)
        self.assertEqual(['e', 'f', 'g', 'h'], [x.winner_id for x in matches])
        matches = scenario_utility.create_match_scenario(unplayed_matches, 5)
        self.assertEqual(['e', 'b', 'g', 'd'], [x.winner_id for x in matches])
        matches = scenario_utility.create_match_scenario(unplayed_matches, 10)
        self.assertEqual(['a', 'f', 'c', 'h'], [x.winner_id for x in matches])
