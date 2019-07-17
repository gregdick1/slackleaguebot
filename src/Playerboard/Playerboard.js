import React, { Component } from 'react';
import Group from './Group'

import { DragDropContext } from "react-beautiful-dnd";
import './Playerboard.css'
import axios from 'axios'

function groupBy(arr, property) {
  return arr.reduce(function(memo, x) {
    if (!memo[x[property]]) { memo[x[property]] = []; }
    memo[x[property]].push(x);
    return memo;
  }, {});
}

class Playerboard extends Component {
  constructor(props) {
      super(props);
      this.state = {
        groups: [],
        user_id: 1
      }
  }

  async componentDidMount() {
    var players = await axios.get(`get-active-players`);   
    var groups = groupBy(players.data, "group");

    groups.Trash = [];

    this.setState({
      groups
    })
  }

  addPlayer = (group_index, playerName) => {
    var updatedGroup = this.state.groups[group_index];

    updatedGroup.push({
      name: playerName,
      group: group_index,
      games_lost: 0,
      games_won: 0,
      sets_lost: 0,
      sets_won: 0,
      slack_id: this.state.user_id
    })

    var updatedGroups = this.state.groups;
    updatedGroups[group_index] = updatedGroup;

    this.setState({
      groups: updatedGroups,
      user_id: this.state.user_id + 1
    })
  }

  onDragEnd = (result) => {
    // dropped outside the list
    if (!result.destination) {
      return;
    }

    var updatedGroups = this.state.groups;

    var removedGroup = this.state.groups[result.source.droppableId];
    var addedGroup = this.state.groups[result.destination.droppableId];

    var movedPlayer = removedGroup[result.source.index]

    // Removing from source
    removedGroup.splice(result.source.index, 1)
    updatedGroups[result.source.droppableId] = removedGroup;

    // Adding to destination
    addedGroup.splice(result.destination.index, 0, movedPlayer)
    updatedGroups[result.destination.droppableId] = addedGroup;

    this.setState({
      groups: updatedGroups
    });
  }

  submitPlayers = async () => {
    console.log(this.state.groups)

    await axios.post('submit-players', { players: this.state.groups, deletedPlayers: this.state.groups.Trash })

    alert("success")
  }

  render() {
    return (
      <div className="groups-container">
        <DragDropContext onDragEnd={this.onDragEnd}>
          {
            Object.entries(this.state.groups).map((group_object_array) => 
              <Group players={group_object_array[1]} dragId={group_object_array[0]} addPlayer={this.addPlayer} />
            )
          }
        </DragDropContext>

        <button id="submit-button" className="btn btn-primary btn-lg" onClick={this.submitPlayers}>Submit</button>
      </div>
    );
  }

}

export default Playerboard;
