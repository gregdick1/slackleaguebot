import React, { useState, useEffect } from 'react'
import { Envelope, EnvelopeCheck } from 'react-bootstrap-icons';
import './MatchDisplay.css'

function MatchDisplay({ match, names }) {
    let p1_score = match.winner_id === null ? '' : ''+match.player_1_score;
    let p2_score = match.winner_id === null ? '' : ''+match.player_2_score;
    let tie_score = match.winner_id === null ? '' : ''+match.tie_score;

    const p_name = (p_id) => {
        if (p_id === null) {
            return "Bye"
        }
        return names[p_id] || p_id
    }
    return (
        <div className="match-item">
            <div className="match-group">
                <div>{match.grouping}</div>
                <div>
                    {match.message_sent === 1 &&
                        <EnvelopeCheck size={14} style={{color:'green'}} />
                    }
                    {match.message_sent !== 1 &&
                        <Envelope size={14} />
                    }
                </div>
            </div>
            <div>
                <div>{p_name(match.player_1_id)}</div>
                <div>{p_name(match.player_2_id)}</div>
            </div>
            <div>
                <div>{p1_score}</div>
                <div>{p2_score}</div>
                {match.play_all_sets === 1 && <div>{tie_score}</div>}
            </div>

        </div>
    );
}

export default MatchDisplay;
