import React, { Component } from 'react';
import { confirmAlert } from 'react-confirm-alert';
import 'react-confirm-alert/src/react-confirm-alert.css';
import axios from 'axios'

import './App.css';

const weeklyCommands = {
  seasonStart: "The next season starts June 3rd. By receiving this message, you will be entered automatically. If you don't want to participate, please let <@U04QW49D1> know asap if you haven't already.",
  standingsUpdated: "Standings for season 3 have been updated. Please finish remaining matches before July 12th. You can view them here: https://sync.hudlnet.com/pages/viewpage.action?pageId=135990683",

  mondayReminderMessage: "This week, you play against <@'+against_user+'>. Please message them _today_ to find a time that works. After your match, report the winner and # of sets (best of 3) to <@UGP9FEBLY> in <#C03NHDHBD>.",
  thursdayReminderMessage: "Friendly reminder that you have a match against <@'+against_user+'>. Please work with them to find a time to play."
}

class App extends Component {
  constructor(props) {
      super(props);
      this.state = {
        message: "",
        response: ""
      }
  }

  changeMessage = (e) => {
    this.setState({
      message: e.target.value
    });
  }

  populateSeasonStarts = () => {
    this.setState({
      message: weeklyCommands.seasonStart
    })
  }
  populateStandingsUpdated = () => {
    this.setState({
      message: weeklyCommands.standingsUpdated
    })
  }
  populateMondayReminder = () => {
    this.setState({
      message: weeklyCommands.mondayReminderMessage
    })
  }
  populateThursdayReminder = () => {
    this.setState({
      message: weeklyCommands.thursdayReminderMessage
    })
  }

  sendDebugMessage = async (e) => {
    var response = await axios.post(`send-debug-message`, { message: this.state.message })

    this.setState({
      response: response.data
    })
  }

  sendRealMessage = async () => {
    var response = await axios.post(`send-real-message`, { message: this.state.message })

    this.setState({
      response: response.data
    })
  }

  confirmRealMessage = () => {
    confirmAlert({
      title: 'Confirm to send messages',
      message: 'Are you sure you want to do this Cam.',
      buttons: [
        {
          label: 'Yes',
          onClick: this.sendRealMessage
        },
        {
          label: 'No'
        }
      ]
    });
  }

  render() {
    const { message, response } = this.state;

    return (
      <div id="main-content">
        <div id="button-wrapper">
          <button className="btn btn-secondary" onClick={this.populateSeasonStarts}>Season Starts</button>
          <button className="btn btn-secondary" onClick={this.populateStandingsUpdated}>Standings Updated</button>
          <button className="btn btn-secondary" onClick={this.populateMondayReminder}>Monday Reminder</button>
          <button className="btn btn-secondary" onClick={this.populateThursdayReminder}>Thursday Reminder</button>
        </div>

        <div className="form-group textarea-wrapper">
          <textarea class="form-control form-rounded" rows="2" value={message} onChange={this.changeMessage}></textarea>
        </div>

        <div id="submit-options">
          <button className="btn btn-secondary" onClick={this.sendDebugMessage}>Send Debug Message</button>
          <button className="btn btn-danger" onClick={this.confirmRealMessage}>Send Real Message</button>
        </div>

        <div className="form-group response-textarea-wrapper">
          <textarea disabled="disabled" class="form-control form-rounded" rows="15" value={response}></textarea>
        </div>
      </div>
    );
  }
}

export default App;
