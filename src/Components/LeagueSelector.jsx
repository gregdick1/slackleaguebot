import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"

import './LeagueSelector.css'

function LeagueSelector() {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        var leaguesResponse = await axios.get(`get-leagues-to-admin`);
        var currentLeagueResponse = await axios.get('get-current-league');
        var leagues = leaguesResponse.data;
        var selectedLeague = currentLeagueResponse.data;

        dispatch({ type: "league_changed", selectedLeague, leagues })
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

    return (
      <span>
          <label>Current League: </label>
          <select name='selectedLeague' value={leagueState.selectedLeague} onChange={handleLeagueChange}>
            {leagueState.leagues.map((league) => (
              <option value={league}>{league}</option>
            ))}
          </select>
      </span>
    );
}

export default LeagueSelector;
