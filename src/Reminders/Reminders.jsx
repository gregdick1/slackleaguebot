import React, { useState, useEffect } from 'react'
import { confirmAlert } from 'react-confirm-alert';
import { Calendar } from "react-multi-date-picker";
import DatePanel from "react-multi-date-picker/plugins/date_panel"
import 'react-confirm-alert/src/react-confirm-alert.css';
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import DbUpdater from "../Components/DbUpdater"

import './Reminders.css';
import './Loader.css'

const weeklyCommands = {
  seasonStart: "The next season starts June 3rd. By receiving this message, you will be entered automatically. If you don't want to participate, please let <@U04QW49D1> know asap if you haven't already.",
  standingsUpdated: "Standings for season 3 have been updated. Please finish remaining matches before July 12th. You can view them here: https://sync.hudlnet.com/pages/viewpage.action?pageId=135990683",

  mondayReminderMessage: "This week, you play against @against_user. Please message them _today_ to find a time that works. After your match, report the winner and # of sets (best of 3) to <@UGP9FEBLY> in <#C03NHDHBD>.",
  thursdayReminderMessage: "Friendly reminder that you have a match against @against_user. Please work with them to find a time to play."
}

function Reminders() {
    const [ message, setMessage ] = useState('')
    const [ response, setResponse ] = useState('')
    const [ loading, setLoading ] = useState(false)

    const [season, setSeason] = useState(-1)
    const [seasons, setSeasons] = useState([])
    const [seasonReminders, setSeasonReminders] = useState([])

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        if (!leagueState.selectedLeague) return

        let seasons = (await axios.get('get-all-seasons', { params: { leagueName: leagueState.selectedLeague } })).data
        setSeasons(seasons)
        let seasonToLoad = season
        if (seasonToLoad === -1) {
          seasonToLoad = seasons[seasons.length-1]
          setSeason(seasonToLoad)
        }
        var reminderDays = (await axios.get('get-reminder-days', {params: { leagueName: leagueState.selectedLeague, season: seasonToLoad }})).data
        const tmp = reminderDays.map(rd => new Date(rd['date']).toISOString())
        setSeasonReminders(tmp)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.lastRefreshed, season]);

    const updateReminderDays = (values) => {
      const isoStrings = values.map(v => new Date(v.year, v.month-1, v.day).toISOString())
      const updateServer = async () => {
        await axios.post('update-reminder-days', { leagueName: leagueState.selectedLeague, season: season, dates: isoStrings })
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
      }
      updateServer().catch(console.error);
      setSeasonReminders(isoStrings)
    }

    const sendMessage = (endpoint) => {
      setResponse('')
      setLoading(true)

      const updateServer = async () => {
        var response = await axios.post(endpoint, { leagueName: leagueState.selectedLeague, message: message })
        setResponse(response.data)
        setLoading(false)
      }
      updateServer().catch(console.error);
    }

    const sendDebugMessage = () => {
      sendMessage('send-debug-message')
    }

    const sendRealMessage = () => {
      sendMessage('send-real-message')
    }

    const confirmRealMessage = () => {
      confirmAlert({
        title: 'Confirm to send messages',
        message: 'Are you sure you want to do this?',
        buttons: [
          {
            label: 'Yes',
            onClick: sendRealMessage
          },
          {
            label: 'No'
          }
        ]
      });
    }

    const dates = seasonReminders.map(sr => new Date(sr))

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div>
        <div className="reminders-controls">
          <div className="season-control">
            <span>Matches from season: </span>
            <select name='selectedSeason' value={season} onChange={(e) => setSeason(e.target.value)}>
              {seasons.map((s) => (
                  <option value={s}>{s}</option>
                ))}
            </select>
          </div>
        </div>
        <div id="main-content" className={loading ? "loading" : null}>
          <Calendar multiple={true} value={dates} onChange={updateReminderDays}
            plugins={[
              <DatePanel sort="date" />
            ]}
          />
          <div id="button-wrapper">
            <button className="btn btn-secondary" onClick={() => setMessage(weeklyCommands.seasonStart)}>Season Starts</button>
            <button className="btn btn-secondary" onClick={() => setMessage(weeklyCommands.standingsUpdated)}>Standings Updated</button>
            <button className="btn btn-secondary" onClick={() => setMessage(weeklyCommands.mondayReminderMessage)}>Monday Reminder</button>
            <button className="btn btn-secondary" onClick={() => setMessage(weeklyCommands.thursdayReminderMessage)}>Thursday Reminder</button>
          </div>

          <div className="form-group textarea-wrapper">
            <textarea class="form-control form-rounded" rows="2" value={message} onChange={(e) => setMessage(e.target.value)}></textarea>
          </div>

          <div id="submit-options">
            <button className="btn btn-secondary" onClick={sendDebugMessage}>Send Debug Message</button>
            <button className="btn btn-danger" onClick={confirmRealMessage}>Send Real Message</button>
          </div>

          <div className={`form-group response-textarea-wrapper ${loading ? "loading" : null}`}>
            { loading && <div class="lds-roller"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div> }
            <textarea disabled="disabled" class="form-control form-rounded" rows="20" value={response}></textarea>
          </div>
        </div>
      </div>
    );
}

export default Reminders;