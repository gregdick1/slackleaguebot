import React, { useState, useEffect } from 'react'
import { Envelope, EnvelopeCheck } from 'react-bootstrap-icons';
import './MatchDisplay.css'

function MatchDisplay({ match, allPlayers }) {
    let p1_score = ''+match.player_1_score;
    let p2_score = ''+match.player_2_score;
    let tie_score = ''+match.tie_score;

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
