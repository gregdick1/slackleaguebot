import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import './MatchEditor.css'

function MatchEditor({ match, allPlayers }) {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {

      }

      fetchData().catch(console.error);
    }, [leagueState.checkForCommandsToRun]);

    const clearScore = () => {
      const updateServer = async () => {
        await axios.post(`clear-score`, { leagueName: leagueState.selectedLeague, matchId: match.id });
        // TODO Probably wanna grab the match from the db again
        match.winner_id = null
        match.sets = 0
        match.date_played = null
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
      }
      updateServer().catch(console.error);
    }

    let p1_score = '';
    let p2_score = '';
    if (match.player_1_id === match.winner_id && match.winner_id !== null) {
        p1_score = ''+match.sets_needed
        p2_score = ''+(match.sets - match.sets_needed)
    } else if (match.player_2_id === match.winner_id && match.winner_id !== null) {
        p1_score = ''+(match.sets - match.sets_needed)
        p2_score = ''+match.sets_needed
    }

    const p_name = (p_id) => {
        if (p_id === null) {
            return "Bye"
        }
        for (var p of allPlayers) {
            if (p.slack_id === p_id) return p.name
        }
        return p_id
    }
    return (
        <div className="match-item">
            <div className="match-group">{match.grouping}</div>
            <div>
                <div>{p_name(match.player_1_id)}</div>
                <div>{p_name(match.player_2_id)}</div>
            </div>
            <div>
                <div>{p1_score}</div>
                <div>{p2_score}</div>
            </div>
            <div>
              { match.winner_id !== null &&
                <button onClick={clearScore}>Clear Score</button>
              }
            </div>

        </div>
    );
}

export default MatchEditor;
