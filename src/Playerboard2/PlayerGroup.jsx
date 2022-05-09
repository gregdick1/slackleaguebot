import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

import { LeagueContext } from "../contexts/League"

function PlayerGroup({players, dragId, addPlayer}) {
    const [addingPlayer, setAddingPlayer] = useState(false)
    const [addPlayerName, setAddPlayerName] = useState("")

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    const onReturn = (e) => {
        if(e.keyCode == 13){
            addPlayer(dragId, e.target.value)
            setAddPlayerName("")
            setAddingPlayer(false)
        }
     }

    return (
        <Droppable droppableId={dragId}>
            {(provided, snapshot) => (
            <div {...provided.droppableProps} ref={provided.innerRef} className="group-wrapper" >
                <div className="group-title">
                    Group {dragId}
                </div>

                {players && players.map((player, index) => (
                <Draggable key={player.slack_id} draggableId={player.slack_id} index={index} className="player-box">
                    {(provided, snapshot) => (
                        <div className="player-in-group" ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} >
                            <div>{player.name}</div>
                            <div>{player.group} {player.games_won}-{player.games_lost} ({player.sets_won}-{player.sets_lost})</div>
                        </div>
                    )}
                </Draggable>
                ))}
                { provided.placeholder }

                <div className="add-player" onClick={() => setAddingPlayer(true)}>
                    {
                        addingPlayer ?
                            <input type="text"
                              onBlur={() => setAddingPlayer(false)}
                              onKeyDown={onReturn}
                              value={addPlayerName}
                              onChange={(e) => setAddPlayerName(e.target.value)}
                              autoFocus/> :
                            <span>Add Player..</span>
                    }
                </div>
            </div>
            )}
        </Droppable>
    );
}

export default PlayerGroup;
