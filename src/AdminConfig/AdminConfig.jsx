import React, { useState, useEffect } from 'react'
import axios from 'axios'

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
        selectedLeague: "",
        leagues:[],
        leagueAdminConfigs:{...blankConfigs},
        newLeagueName:""
    })

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        var leaguesResponse = await axios.get(`get-leagues-to-admin`);
        var currentLeagueResponse = await axios.get('get-current-league');
        var leagues = leaguesResponse.data;
        var selectedLeague = currentLeagueResponse.data;
        var configsResponse = await axios.get('get-league-admin-configs', { params: { leagueName: selectedLeague } })
        var leagueAdminConfigs = configsResponse.data;
        setState({
          ...state,
          selectedLeague,
          leagues,
          leagueAdminConfigs
        });
      }

      fetchData().catch(console.error);
    }, []);

    const handleLeagueChange = (e) => {
      const { value } = e.target;
      const updateServer = async () => {
        await axios.post(`set-current-league`, { selectedLeague: value });
        var configsResponse = await axios.get('get-league-admin-configs', { params: { leagueName: value } })
        var leagueAdminConfigs = configsResponse.data;
        setState({
          ...state,
          selectedLeague: value,
          leagueAdminConfigs
        });
      }

      updateServer().catch(console.error);
    }

    const handleNewLeague = (e) => {
      const { value, name } = e.target;
      let newLeagueName = state.newLeagueName
      if (newLeagueName === "") {
        alert("Must enter a name for the league.");
        return;
      } else if (state.leagues.includes(newLeagueName)) {
        alert("You already have a league with that name.");
        return;
      }

      let leagueAdminConfigs = name === 'copyLeague' ? {...state.leagueAdminConfigs} : {...blankConfigs}

      const updateServer = async () => {
        await axios.post(`add-league`, { newLeagueName, leagueAdminConfigs });
        await axios.post(`set-current-league`, { selectedLeague: newLeagueName });
        var leagues = [...state.leagues]
        leagues.push(newLeagueName)

        setState({
          ...state,
          selectedLeague: newLeagueName,
          leagueAdminConfigs,
          leagues,
          newLeagueName: ""
        });
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
                selectedLeague: state.selectedLeague,
                configKey: inputProps.name,
                configValue: val
            });
    }

    console.log(state)

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

    const editExisting = state.leagues.length > 0;

    return (
      <div id="main-content" className="main-content">
        <div id="league-selector">
          <label>Select League to Admin</label>
          <select name='selectedLeague' value={state.selectedLeague} onChange={handleLeagueChange}>
            {state.leagues.map((league) => (
              <option value={league}>{league}</option>
            ))}
          </select>
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
        </div>

        { editExisting && editor('Server Host', 'SERVER_HOST') }
        { editExisting && editor('Server Port', 'SERVER_PORT') }
        { editExisting && editor('Server User', 'SERVER_USER') }
        { editExisting && editor('Bot Command', 'BOT_COMMAND') }


      </div>
    );
}

export default AdminConfig;
