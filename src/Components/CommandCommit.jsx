import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"

import './CommandCommit.css'

function CommandCommit() {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ committing, setCommitting] = useState(false)
    const [ numCommands, setNumCommands] = useState(0)

    useEffect(() => {
      const fetchData = async () => {
        var commandsResponse = await axios.get('get-commands-to-run', { params: { leagueName: leagueState.selectedLeague }});
        setNumCommands(commandsResponse.data)
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:false})
      }

      fetchData().catch(console.error);
    }, [leagueState.checkForCommandsToRun]);

    const handleCommit = () => {
      const updateServer = async () => {

        if (!window.confirm("Are you sure you want to push these updates?")) {
          return;
        }

        setCommitting(true)
        let response = await axios.post('push-updates-to-server', { leagueName: leagueState.selectedLeague });
        setCommitting(false)
        if (response.data['success']) {
          var lastRefreshedResponse = await axios.get('get-last-db-refresh', { params: { leagueName: leagueState.selectedLeague }});
          var lastRefreshed = lastRefreshedResponse.data;
          dispatch({ type: "db_refreshed", lastRefreshed})
          dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        } else {
          alert("Update failed: "+response.data['message'])
        }
      }

      updateServer().catch(console.error)
    }

    return (
      <span>
          <label>Updates to commit: </label><span>{numCommands}</span>
          <button disabled={committing} onClick={handleCommit}>Push to server</button>
          { committing &&
              <div className="spinner-container">
                <div className="loading-spinner">
                </div>
              </div>
          }
      </span>
    );
}

export default CommandCommit;
