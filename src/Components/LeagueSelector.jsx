import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import LastRefresh from "./LastRefresh"

import './LeagueSelector.css'

function LeagueSelector() {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ refreshing, setRefreshing] = useState(false)

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        var leaguesResponse = await axios.get(`get-leagues-to-admin`);
        var currentLeagueResponse = await axios.get('get-current-league');
        var leagues = leaguesResponse.data;
        var selectedLeague = currentLeagueResponse.data;

        var lastRefreshedResponse = await axios.get('get-last-db-refresh', { params: { leagueName: selectedLeague }});
        var lastRefreshed = lastRefreshedResponse.data;

        dispatch({ type: "league_changed", selectedLeague, leagues })
        dispatch({ type: "db_refreshed", lastRefreshed})
      }

      fetchData().catch(console.error);
    }, []);

    const handleLeagueChange = (e) => {
      const { value } = e.target;
      const updateServer = async () => {
        await axios.post(`set-current-league`, { selectedLeague: value });

        dispatch({ type: "league_changed", selectedLeague: value, leagues: [...leagueState.leagues] })
      }

      updateServer().catch(console.error);
    }

    const handleRefreshDb = (e) => {
      setRefreshing(true)
      const updateServer = async () => {
        let response = await axios.post('refresh-db', { leagueName: leagueState.selectedLeague })
        setRefreshing(false)
        if (response.data['success']) {
          var lastRefreshedResponse = await axios.get('get-last-db-refresh', { params: { leagueName: leagueState.selectedLeague }});
          var lastRefreshed = lastRefreshedResponse.data;
          dispatch({ type: "db_refreshed", lastRefreshed})
        } else {
          alert("Refresh failed: "+response.data['message'])
        }
      }

      updateServer().catch(console.error)
    }

    return (
      <span>
          <label>Current League: </label>
          <select name='selectedLeague' value={leagueState.selectedLeague} onChange={handleLeagueChange}>
            {leagueState.leagues.map((league) => (
              <option value={league}>{league}</option>
            ))}
          </select>
          <button name='refresh_db' onClick={handleRefreshDb}>Refresh DB</button>
          { refreshing &&
            <div className="spinner-container">
              <div className="loading-spinner">
              </div>
            </div>
          }
          <LastRefresh />
      </span>
    );
}

export default LeagueSelector;
