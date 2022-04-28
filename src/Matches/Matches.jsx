import React, { Component } from 'react'
import axios from 'axios'

import './Matches.css'
import groupBy from '../helpers.js'

class Matches extends Component {
    constructor(props) {
        super(props);
        this.state = {
            groups: [],
            playerOneID: '',
            playerOneIDInputOpen: false,
            playerTwoID: '',
            playerTwoIDInputOpen: false,
            winnerID: '',
            winnerIDInputOpen: false,
            group: '',
            groupInputOpen: false,
            week: '',
            weekInputOpen: false,
            sets: null,
            setsInputOpen: false,
        }
    }
    /*
        groups: {
            week: [
                {
                    grouping: string,
                    player_1_id: string,
                    player_2_id: string,
                    winner_id: null | string,
                    week: string,
                    sets: number
                }
            ]
        }
    */

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
       const inputName = `${name}InputOpen`
       this.setState({
          [inputName]: !this.state[inputName]
       })
    }

    updateValue = (e) => {
        const { name, value } = e.target;
        this.setState({
            [name]: value
        })
    }

    render() {
    console.log(this.state)
      return (
        <div className="groups-container">
          {
            Object.entries(this.state.groups).map((group_object_array, index) =>
              <div className="group-wrapper">
                <div className="group-title">
                    <input className="group-week-container" type="text" name= {index} value={!!this.state.index ? this.state.index.date : group_object_array[0]} onChange={this.handleChange} />
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
                                    <label for="recipient-name">Player 1 ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="playerOneID" value={ this.state.playerOneIDInputOpen ? this.state.playerOneID : match.player_1_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="recipient-name">Player 2 ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="playerTwoID" value={ this.state.playerTwoIDInputOpen ? this.state.playerTwoID : match.player_2_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="recipient-name">Group</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="group" value={ this.state.groupInputOpen ? this.state.group : match.grouping } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="recipient-name">Winner ID</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="winnerID" value={ this.state.winnerIDInputOpen ? this.state.winnerID : match.winner_id } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="recipient-name">Week</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="text" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="week" value={ this.state.weekInputOpen ? this.state.week : match.week } onChange={this.updateValue} autoFocus />
                                    </div>

                                    <label for="recipient-name">Sets</label>
                                    <div onClick={this.toggleTextBox}>
                                        <input type="number" onBlur={this.toggleTextBox} class="form-control" id="recipient-name" name="sets" value={ this.state.setsInputOpen ? this.state.sets : match.sets } onChange={this.updateValue} autoFocus />
                                    </div>
                                  </div>
                              </form>
                          </div >
                          <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary">Save changes</button>
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
