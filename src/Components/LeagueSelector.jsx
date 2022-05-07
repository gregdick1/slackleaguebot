import React, { useState, useEffect } from 'react'
import { Download } from 'react-bootstrap-icons';
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import LastRefresh from "./LastRefresh"
import CommandCommit from "./CommandCommit"
import Spinner from "./Spinner"

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
        var leagueConfigsResponse = await axios.get('get-league-admin-configs', { params: { leagueName: selectedLeague }});

        var lastRefreshed = lastRefreshedResponse.data;
        var leagueConfigs = leagueConfigsResponse.data;

        dispatch({ type: "league_changed", selectedLeague, leagues })
        dispatch({ type: "db_refreshed", lastRefreshed})
        dispatch({ type: "db_connection_status", hasConnected: leagueConfigs['HAS_CONNECTED'], hasDeployed: leagueConfigs['HAS_DEPLOYED']})
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.hasDeployed]);

    const handleLeagueChange = (e) => {
      const { value } = e.target;
      const updateServer = async () => {
        await axios.post(`set-current-league`, { selectedLeague: value });

        dispatch({ type: "league_changed", selectedLeague: value, leagues: [...leagueState.leagues] })
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
      }

      updateServer().catch(console.error);
    }

    const handleRefreshDb = (e) => {
      const updateServer = async () => {
        var commandsResponse = await axios.get('get-commands-to-run', { params: { leagueName: leagueState.selectedLeague }});
        var commands = commandsResponse.data;
        var doRefresh = commands === 0 || window.confirm("You have unsaved updates locally. This will overwrite them with the db from the server.")
        if (!doRefresh) return

        setRefreshing(true)
        let response = await axios.post('refresh-db', { leagueName: leagueState.selectedLeague })
        setRefreshing(false)
        if (response.data['success']) {
          var lastRefreshedResponse = await axios.get('get-last-db-refresh', { params: { leagueName: leagueState.selectedLeague }});
          var lastRefreshed = lastRefreshedResponse.data;
          dispatch({ type: "db_refreshed", lastRefreshed})
          dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        } else {
          alert("Refresh failed: "+response.data['message'])
        }
      }

      updateServer().catch(console.error)
    }

    return (
      <div className="league-controls">
        <div className="league-selector nav-control">
          <div>Current League</div>
          <div>
            <select name='selectedLeague' value={leagueState.selectedLeague} onChange={handleLeagueChange}>
              {leagueState.leagues.map((league) => (
                <option value={league}>{league}</option>
              ))}
            </select>
          </div>
        </div>
        { leagueState.hasConnected && leagueState.hasDeployed &&
        <div className="nav-control refresh-control">
          <button
            name='refresh_db'
            className="btn btn-nav-control"
            disabled={refreshing}
            onClick={handleRefreshDb}
            title="Download the db from the server to get the most up to date data.">
            { refreshing &&
              <Spinner size={20} />
            }
            { !refreshing &&
              <Download size={20} />
            }

          </button>
        </div>
        }
        { leagueState.hasConnected && leagueState.hasDeployed &&
          <LastRefresh />
        }
        { leagueState.hasConnected && leagueState.hasDeployed &&
          <CommandCommit />
        }
      </div>
    );
}

export default LeagueSelector;
