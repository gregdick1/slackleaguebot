import React, { useState, useEffect } from 'react'
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import EdiText from 'react-editext';
import './AdminConfig.css'

function AdminConfig() {

    const blankConfigs = {
        SERVER_HOST: 'hostname',
        SERVER_PORT: '22',
        SERVER_USER: 'user',
        BOT_COMMAND: 'python'
    }
    const [state, setState] = useState({
        leagueAdminConfigs:{...blankConfigs},
        newLeagueName:""
    })

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        var configsResponse = await axios.get('get-league-admin-configs', { params: { leagueName: leagueState.selectedLeague } })
        var leagueAdminConfigs = configsResponse.data;
        setState({
          ...state,
          leagueAdminConfigs
        });
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague]);

    const handleNewLeague = (e) => {
      const { value, name } = e.target;
      let newLeagueName = state.newLeagueName
      if (newLeagueName === "") {
        alert("Must enter a name for the league.");
        return;
      } else if (leagueState.leagues.includes(newLeagueName)) {
        alert("You already have a league with that name.");
        return;
      }

      let leagueAdminConfigs = name === 'copyLeague' ? {...state.leagueAdminConfigs} : {...blankConfigs}

      const updateServer = async () => {
        await axios.post(`add-league`, { newLeagueName, leagueAdminConfigs });
        await axios.post(`set-current-league`, { selectedLeague: newLeagueName });
        var leagues = [...leagueState.leagues]
        leagues.push(newLeagueName)

        setState({
          ...state,
          leagueAdminConfigs,
          newLeagueName: ""
        });
        dispatch({ type: "league_changed", selectedLeague: newLeagueName, leagues })
      }
      updateServer().catch(console.error);
    }

    const handleSave = async (val, inputProps) => {
        var leagueAdminConfigs = {...state.leagueAdminConfigs, [inputProps.name]: val}
        setState({
          ...state,
          leagueAdminConfigs
        })
        const response = await axios.post('set-league-admin-config', {
                selectedLeague: leagueState.selectedLeague,
                configKey: inputProps.name,
                configValue: val
            });
    }

    const editor = (label, config) => {
      return (
      <div className="inline-editor">
        <label>{label}:</label>
        <EdiText
          className="editext-editor"
          type="text"
          value={state.leagueAdminConfigs[config]}
          onSave={handleSave}
          inputProps={{ name: config }}
          containerProps={{ style: { display: 'inline-block' } }}
        />
      </div>
      );
    }

    const editExisting = leagueState.leagues.length > 0;

    return (
      <div id="main-content" className="main-content">
          <div className="new-league-inputs">
            <div>
              <label>Create New League</label>
              <input type="text" value={state.newLeagueName}
                    onChange={e =>
                          setState({
                            ...state,
                            newLeagueName: e.target.value
                          })
                    }
              />
            </div>
            <div>
              <button name="newLeague" className="btn btn-primary btn-lg" onClick={handleNewLeague}>Create League</button>
              {editExisting &&
              <button name="copyLeague" className="btn btn-primary btn-lg" onClick={handleNewLeague}>Copy Current League</button>
              }
            </div>
          </div>
        <div className="tab-header">
          <label>Admin Configuration for League: {leagueState.selectedLeague}</label>
        </div>
        { editExisting && editor('Server Host', 'SERVER_HOST') }
        { editExisting && editor('Server Port', 'SERVER_PORT') }
        { editExisting && editor('Server User', 'SERVER_USER') }
        { editExisting && editor('Bot Command', 'BOT_COMMAND') }


      </div>
    );
}

export default AdminConfig;
