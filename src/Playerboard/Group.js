import React, { Component } from 'react';
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

export default class Group extends Component {
    constructor(props) {
        super(props);
        this.state = {
          addPlayerOpen: false,
          playerName: ""
        }
    }

    toggleTextbox = () => {
        this.setState({
            addPlayerOpen: !this.state.addPlayerOpen
        })
    }

    changeName = (e) => {
        this.setState({
            playerName: e.target.value
        })
    }

    onReturn = (e) => {
        if(e.keyCode == 13){
            this.props.addPlayer(this.props.dragId, e.target.value)

            this.setState({
                addPlayerOpen: false,
                playerName: "",
            })
        }
     }

    render() {
        var playerOpen = this.state.addPlayerOpen

        return (
            <Droppable droppableId={this.props.dragId}>
                {(provided, snapshot) => (
                <div
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    className="group-wrapper"
                >
                    <div className="group-title">
                        Group {this.props.dragId}
                    </div>

                    {this.props.players && this.props.players.map((player, index) => (
                    <Draggable key={player.slack_id} draggableId={player.slack_id} index={index} className="player-box">
                        {(provided, snapshot) => (
                            <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                {...provided.dragHandleProps}
                            >
                                {player.name} {player.group} {player.games_won}-{player.games_lost} ({player.sets_won}-{player.sets_lost})
                            </div>
                        )}
                    </Draggable>
                    ))}
                    { provided.placeholder }

                    <div className="add-player" onClick={this.toggleTextbox}>
                        { 
                            playerOpen ? 
                                <input type="text" onBlur={this.toggleTextbox} onKeyDown={this.onReturn} value={this.state.playerName} onChange={this.changeName} autoFocus/> :
                                <span>Add Player..</span>
                        }
                    </div>
                </div>
                )}
            </Droppable>
        );
    }
}
