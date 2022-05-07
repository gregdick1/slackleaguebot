import React, { useState, useEffect } from 'react'

import './MatchDisplay.css'

function MatchDisplay({ match, allPlayers }) {
    let p1_score = '';
    let p2_score = '';
    if (match.player_1_id == match.winner_id) {
        p1_score = ''+match.sets_needed
        p2_score = ''+(match.sets - match.sets_needed)
    } else if (match.player_2_id == match.winner_id) {
        p1_score = ''+(match.sets - match.sets_needed)
        p2_score = ''+match.sets_needed
    }

    const p_name = (p_id) => {
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

        </div>
    );
}

export default MatchDisplay;
