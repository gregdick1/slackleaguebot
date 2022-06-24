import React, { useState, useEffect } from 'react'
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import DbUpdater from "../Components/DbUpdater"
import './LocalUpdates.css'

function LocalUpdates() {
    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ commands, setCommands ] = useState([])

    useEffect(() => {
      const fetchData = async () => {
        var response = await axios.get('get-local-updates', {params: { leagueName: leagueState.selectedLeague }})
        console.log(response)
        setCommands(response.data)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.lastRefreshed]);

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div id="main-content" className="main-content">
        <div className="local-updates">
        {commands.map(c => (
          <div>{c}</div>
        ))}
        </div>
      </div>
    );
}

export default LocalUpdates;
