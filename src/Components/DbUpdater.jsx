import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import Spinner from "../Components/Spinner"

import './DbUpdater.css'

function DbUpdater() {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ updateStatus, setUpdateStatus ] = useState({})
    const [ updating, setUpdating ] = useState(false)

    useEffect(() => {
      const fetchData = async () => {
        var status = (await axios.get('get-db-update-status', { params: { leagueName: leagueState.selectedLeague }})).data
        setUpdateStatus(status)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague]);

    const handleUpdate = () => {
      const updateServer = async () => {
        setUpdating(true)
        let response = await axios.post('update-db', { leagueName: leagueState.selectedLeague });
        setUpdating(false)
        if (response.data['success']) {
          alert('Update Successful')
          dispatch({ type: 'need_db_update', needDbUpdate: false })
        } else {
          alert("Update failed: "+response.data['message'])
        }
      }

      updateServer().catch(console.error)
    }

    return (
      <div className="db-updater">
          <div>Current League Version: {updateStatus.current_version}</div>
          <div>Latest League Version: {updateStatus.latest_version}</div>
          <div>If this league has already been deployed, this will first apply any remaining updates to commit first. If you don't want to commit those updates, please refresh the db first.</div>
          <div><button disabled={updating} onClick={handleUpdate}>
          { updating &&
            <Spinner size={20}/>
          }
          <span>Update League</span>
          </button></div>
      </div>
    );
}

export default DbUpdater;
