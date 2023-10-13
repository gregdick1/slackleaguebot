import React, { useState, useEffect } from 'react'

import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import ToolTip from "../Components/ToolTip"
import './MatchEditor.css'

function MatchEditor({ match, allPlayers }) {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ reload, setReload ] = useState(false)

    useEffect(() => {
      const fetchData = async () => {
        setReload(false)
      }

      fetchData().catch(console.error);
    }, [leagueState.checkForCommandsToRun, reload]);

    const clearScore = () => {
      const updateServer = async () => {
        await axios.post(`clear-score`, { leagueName: leagueState.selectedLeague, matchId: match.id });
        // TODO Probably wanna grab the match from the db again
        match.winner_id = null
        match.sets = 0
        match.date_played = null
        match.player_1_score = 0
        match.player_2_score = 0
        match.tie_score = 0
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
      }
      updateServer().catch(console.error);
    }

    const setWinner = (winnerId, loserId) => {
      const updateServer = async () => {
        await axios.post(`set-score`, { leagueName: leagueState.selectedLeague, matchId: match.id, winnerId, winnerScore: match.sets_needed, loserScore: 0, tieScore: 0 });
        // TODO Probably wanna grab the match from the db again
        match.winner_id = winnerId
        if(match.winner_id === match.player_1_id) {
          match.player_1_score = match.sets_needed
          match.player_2_score = 0
        }
        else if (match.winner_id === match.player_2_id) {
          match.player_2_score = match.sets_needed
          match.player_1_score = 0
        }
        match.sets = match.sets_needed
        match.tie_score = 0
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        setReload(true)
      }
      updateServer().catch(console.error);
    }

    const updateNonWinnerScore = (winnerId, loserId, loserScore, tieScore) => {
      if (loserScore < 0 || loserScore >= match.sets_needed) return
      if (tieScore < 0 || tieScore > match.sets_needed) return

      const updateServer = async () => {
        let winnerScore = match.play_all_sets === 1 ? match.sets_needed - loserScore - tieScore : match.sets_needed

        await axios.post(`set-score`, { leagueName: leagueState.selectedLeague, matchId: match.id, winnerId, winnerScore, loserScore, tieScore});
        // TODO Probably wanna grab the match from the db again
        if(match.winner_id === match.player_1_id) {
          match.player_1_score = winnerScore
          match.player_2_score = loserScore
          match.tie_score = tieScore
        }
        else if (match.winner_id === match.player_2_id) {
          match.player_2_score = winnerScore
          match.player_1_score = loserScore
          match.tie_score = tieScore
        }
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        setReload(true)
      }
      updateServer().catch(console.error);
    }

    const setMatchForfeit = () => {
      const updateServer = async () => {
        await axios.post(`set-forfeit`, { leagueName: leagueState.selectedLeague, matchId: match.id, forfeit: !match.forfeit });
        // TODO Probably wanna grab the match from the db again
        match.forfeit = !match.forfeit
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        setReload(true)
      }
      updateServer().catch(console.error);
    }

    let p1_score = match.winner_id === null ? '' : ''+match.player_1_score;
    let p2_score = match.winner_id === null ? '' : ''+match.player_2_score;
    let tie_score = match.winner_id === null ? '' : ''+match.tie_score;

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
            <table className="match-editor-table">
              <tr>
                <th>Player</th>
                <th>Score</th>
                <th>Winner</th>
              </tr>
              <tr>
                <td>{p_name(match.player_1_id)}</td>
                <td><input className="score-field" disabled={match.winner_id !== match.player_2_id} type="number" value={p1_score} onChange={(e) => updateNonWinnerScore(match.player_2_id, match.player_1_id, e.target.value, tie_score)} /></td>
                <td><input className="winner-radio" type="radio" name={match.id+"_winner"} checked={match.winner_id === match.player_1_id} onChange={(e) => setWinner(match.player_1_id, match.player_2_id)} /></td>
              </tr>
              <tr>
                <td>{p_name(match.player_2_id)}</td>
                <td><input className="score-field" disabled={match.winner_id !== match.player_1_id} type="number" value={p2_score} onChange={(e) => updateNonWinnerScore(match.player_1_id, match.player_2_id, e.target.value, tie_score)} /></td>
                <td><input className="winner-radio" type="radio" name={match.id+"_winner"} checked={match.winner_id === match.player_2_id} onChange={(e) => setWinner(match.player_2_id, match.player_1_id)} /></td>
              </tr>
              { match.play_all_sets === 1 &&
                <tr>
                <td>Ties</td>
                <td><input className="score-field" type="number" value = {tie_score} onChange={(e) => updateNonWinnerScore(match.player_1_id, match.player_2_id, Math.min(p1_score, p2_score), e.target.value)} /></td>
                </tr>
              }
            </table>

            <div className="edit-match-controls">
              <div>
                <span style={{ marginRight: 5 }}>Was forfeit? <input type="checkbox" checked={match.forfeit} onChange={setMatchForfeit}/></span>
                <ToolTip size={14} width={240} text={"Mark the match as a forfeit. This allows you to set a winner and score for group rank and tie breaker purposes, but the match won't be included in historical and elo data."} />
              </div>
              { match.winner_id !== null &&
                <button onClick={clearScore}>Clear Score</button>
              }
            </div>

        </div>
    );
}

export default MatchEditor;
