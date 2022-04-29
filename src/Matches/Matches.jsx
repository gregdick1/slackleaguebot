import React, { Component } from 'react'
import axios from 'axios'

import './Matches.css'
import groupBy from '../helpers.js'

class Matches extends Component {
    constructor(props) {
        super(props);
        this.state = {
            groups: [],
            player_1_id: '',
            player_1_id_input_open: false,
            player_2_id: '',
            player_2_id_input_open: false,
            winner_id: '',
            winner_id_input_open: false,
            grouping: '',
            grouping_input_open: false,
            week: '',
            week_input_open: false,
            sets: '',
            sets_input_open: false,
        }
    }

    async componentDidMount() {
        const matches = await axios.get('/get-current-matches');
        const groups = groupBy(matches.data, "week")

        this.setState({
            groups
        })

         Object.entries(groups).map((group, index) => {
            const value = {
                date: group[0],
                didUpdate: false
            }

            this.setState({
                ...this.state,
                [index]: value
            })
        })
    }

    handleChange = (e) => {
        const { value, name } = e.target;
        this.setState({
            ...this.state,
            [name]: {
                date: value,
                didUpdate: true,
            }
        })
    }

    toggleTextBox = (e) => {
       const { name } = e.target;
       const inputName = `${name}_input_open`
       this.setState({
          [inputName]: !this.state[inputName]
       })
    }

    updateValue = (e) => {
        const { name, value } = e.target;
        if (name === 'grouping') {
            this.setState({
                [name]: value.toUpperCase()
            })
        } else {
            this.setState({
                [name]: value
            })
        }

    }

    handleSubmit = async (date, index, e) => {
        e.preventDefault();
        const { player_1_id, player_2_id, winner_id, week, grouping, sets, groups } = this.state;
        const matchDetailsArray = [ 'player_1_id', 'player_2_id', 'winner_id', 'week', 'grouping', 'sets' ];
        const singleGroup = Object.entries(groups).find(group => group[0] === date);

        const matchDetails = {
            'player_1_id': player_1_id.length ? player_1_id : singleGroup[1][index].player_1_id,
            'player_2_id': player_2_id.length ? player_2_id : singleGroup[1][index].player_2_id,
            'winner_id': winner_id.length ? winner_id : singleGroup[1][index].winner_id,
            'week': week.length ? week : singleGroup[1][index].week,
            'grouping': grouping.length ? grouping : singleGroup[1][index].grouping,
            'sets': sets.length ? sets : singleGroup[1][index].sets,
            'id': singleGroup[1][index].id
        };

        const response = await axios.post('update-match-info', {...matchDetails})

        matchDetailsArray.map((name) => {
            this.setState({
                [name]: ''
            })
        });

        const matches = await axios.get('/get-current-matches');
        const newGroups = groupBy(matches.data, "week");

        this.setState({
            ...this.state,
            groups: newGroups
        })

        alert(response.data);
    }

    render() {
      return (
        <div className="groups-container">
          {
            this.state.groups &&
            Object.entries(this.state.groups).map((group_object_array, index) =>
              <div className="group-wrapper">
                <div className="group-title">
                    <input className="group-week-container" type="text" name= {index} value={!!this.state[index] ? this.state[index].date : group_object_array[0]} onChange={this.handleChange} />
                </div>
                {group_object_array[1] && group_object_array[1].map((match, index) => (
                <>
                    <div className="match-box" data-toggle="modal" data-target={`#modal-${group_object_array[0]}-${index}`}>
                        <div className="match-item">
                            <div>
                                <div>{match.player_1_id}</div>
                                <div>{match.player_2_id}</div>
                            </div>
                            <div className="match-group">{match.grouping}</div>
                        </div>
                    </div>
                    <div class="modal show" id={`modal-${group_object_array[0]}-${index}`} tabIndex="-1" role="dialog" aria-labelledBy="modalLabel" aria-hidden="true">
                      <div class="modal-dialog modal-dialog-centered" role="document">
                        <div class="modal-content">
                          <div class="modal-header">
                            <h5 class="modal-title" id="modalLabel">Update Match</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                              <span aria-hidden="true">&times;</span>
                            </button>
                          </div>
                          <div class="modal-body">
                              <form>
                                  <div class="form-group">
                                    <label for="player-1-id">Player 1 ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="player-1-id" name="player_1_id" value={ this.state.player_1_id_input_open || this.state.player_1_id.length ? this.state.player_1_id : match.player_1_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="player-2-id">Player 2 ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="player-2-id" name="player_2_id" value={ this.state.player_2_id_input_open || this.state.player_2_id.length ? this.state.player_2_id : match.player_2_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="grouping">Group</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="grouping" name="grouping" value={ this.state.grouping_input_open || this.state.grouping.length ? this.state.grouping : match.grouping } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="winner-id">Winner ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="winner-id" name="winner_id" value={ this.state.winner_id_input_open || this.state.winner_id.length ? this.state.winner_id : match.winner_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="week">Week</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="week" name="week" value={ this.state.week_input_open || this.state.week.length ? this.state.week : match.week } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="sets">Sets</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="number" onBlur={this.toggleTextBox} class="form-control" id="sets" name="sets" value={ this.state.sets_input_open || this.state.sets.length ? this.state.sets : match.sets } onChange={this.updateValue} autoFocus />
                                    </div>
                                  </div>
                              </form>
                          </div >
                          <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" data-dismiss="modal" onClick={e => (this.handleSubmit(group_object_array[0], index, e))}>Save changes</button>
                          </div>
                        </div>
                      </div>
                    </div>
                    </>
                ))}
              </div>
            )
          }
        <button id="submit-button" className="btn btn-primary btn-lg">Submit</button>
      </div>
     );
    }
}

export default Matches;
