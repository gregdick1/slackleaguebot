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

    const triggerReminders = () => {
      const updateServer = async () => {
        var commands = (await axios.get('get-commands-to-run', { params: { leagueName: leagueState.selectedLeague }})).data;
        var doRefresh = commands === 0 || window.confirm("You have unsaved updates locally. This will overwrite them with the db from the server before sending messages.")
        if (!doRefresh) return

        if (commands === 0) {
          doRefresh = window.confirm("This will send real slack messages to real users. Are you sure you want to do this?")
          if (!doRefresh) return
        }

        setLoading(true)
        var response = await axios.post('trigger-reminders', { leagueName: leagueState.selectedLeague })
        setLoading(false)
        if (response.data['success']) {
          var lastRefreshedResponse = await axios.get('get-last-db-refresh', { params: { leagueName: leagueState.selectedLeague }});
          var lastRefreshed = lastRefreshedResponse.data;
          dispatch({ type: "db_refreshed", lastRefreshed})
          dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
          alert("Match messages and reminders succeeded!")
        } else {
          alert("Reminders failed: "+response.data['message'])
        }
      }
      updateServer().catch(console.error);
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
        message: "This will send real slack messages to real users. Are you sure you want to do this?",
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
    const reminderInstr = 'Auto reminders require a cron job to be configured on the server. When a reminder runs, it will look for any unplayed matches with a date <= the date of the reminder. If the match has not had its match message sent yet, it will send the match message. If it has already had a match message sent, it will send a reminder message instead.'

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div className="reminders-container">
        <div className="reminders-controls">
          <div className="season-control">
            <span>Reminders for season: </span>
            <select name='selectedSeason' value={season} onChange={(e) => setSeason(e.target.value)}>
              {seasons.map((s) => (
                  <option value={s}>{s}</option>
                ))}
            </select>
            <button disabled={loading} className="btn btn-secondary btn-trigger-reminders" onClick={triggerReminders}>Manual Trigger Reminders</button>
          </div>
          <Calendar multiple={true} value={dates} onChange={updateReminderDays}
            plugins={[
              <DatePanel sort="date" />
            ]}
          />
          <div className='reminder-instructions'>{reminderInstr}</div>
        </div>
        <div id="custom-message-container" className={loading ? "loading" : null}>
          <div className='custom-title'>Send Custom Message to Active Players</div>
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