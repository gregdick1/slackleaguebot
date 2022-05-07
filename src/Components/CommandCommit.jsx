import React, { useState, useEffect } from 'react'
import { Upload } from 'react-bootstrap-icons';
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import Spinner from "./Spinner"

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
      <div className="nav-control">
          <div>Updates to Commit</div>
          <div className="push-control">
            <span>{numCommands}</span>
            <button
              name='refresh_db'
              className="btn btn-nav-control"
              disabled={numCommands === 0 || committing}
              onClick={handleCommit}
              style={{ padding: "0px 5px 2px 5px" }}
              title="This will download the db from the server, apply the updates to it, then upload it back to the server.">
              { committing &&
                <Spinner size={14}/>
              }
              { !committing &&
                <Upload size={14} />
              }
            </button>
          </div>
      </div>
    );
}

export default CommandCommit;
