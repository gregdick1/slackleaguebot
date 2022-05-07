import React, { useState, useEffect } from 'react'
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import EdiText from 'react-editext';
import Spinner from "../Components/Spinner"

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

    const [connecting, setConnecting] = useState(false)
    const [deploying, setDeploying] = useState(false)
    const [reload, setReload] = useState(false)

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
        setReload(false)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, reload]);

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
        if (leagueAdminConfigs['HAS_CONNECTED'] === 'True') setReload(true)
    }

    const handleTestConnection = (e) => {
      setConnecting(true)
      const fetchData = async () => {
        var response = await axios.post(`check-server-connection`, { leagueName: leagueState.selectedLeague });
        setConnecting(false)
        if (response.data['success']) {
          alert("Connection Succeeded!")
          dispatch({ type: "db_connection_status", hasConnected: true, hasDeployed: state.leagueAdminConfigs['HAS_DEPLOYED']})
          setReload(true)
        } else {
          alert("Connect failed: "+response.data['message'])
        }
      }

      fetchData().catch(console.error);
    }

    const handleDeploy = (e) => {
      setDeploying(true)
      const fetchData = async () => {
        var response = await axios.post(`deploy-to-server`, { leagueName: leagueState.selectedLeague });
        setDeploying(false)
        if (response.data['success']) {
          alert(response.data['message'])
          dispatch({ type: "db_connection_status", hasConnected: state.leagueAdminConfigs['HAS_CONNECTED'], hasDeployed: true})
          setReload(true)
        } else {
          alert("Connect failed: "+response.data['message'])
        }
      }

      fetchData().catch(console.error);
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
          // TODO smaller buttons
//           saveButtonClassName="inline-save-button"
//           editButtonClassName="inline-edit-button"
//           cancelButtonClassName="inline-cancel-button"
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
        { editExisting &&
            <div>
                {editor('Server Host', 'SERVER_HOST')}
                {editor('Server Port', 'SERVER_PORT')}
                {editor('Server User', 'SERVER_USER')}
                {editor('Bot Command', 'BOT_COMMAND')}
                <div>
                  <label>Has Connected?:</label>
                  {state.leagueAdminConfigs['HAS_CONNECTED'] === 'True' ? <span>Yes</span> : <span>No</span>}
                </div>

                <div>
                    <button name="testConnection" disabled={connecting} className="btn btn-primary" onClick={handleTestConnection}>
                      { connecting &&
                        <Spinner size={20} />
                      }
                      <span>Test Connection</span>
                    </button>

                </div>
                <div>
                  <label>Has Deployed?:</label>
                  {state.leagueAdminConfigs['HAS_DEPLOYED'] === 'True' ? <span>Yes</span> : <span>No</span>}
                </div>
                { state.leagueAdminConfigs['HAS_CONNECTED'] === 'True' &&
                  <div>
                    <button name="deploy" disabled={deploying} className="btn btn-primary" onClick={handleDeploy}>
                      { deploying &&
                        <Spinner size={20} />
                      }
                      <span>Deploy or Connect To Existing</span>
                    </button>
                  </div>
                }

            </div>
        }

      </div>
    );
}

export default AdminConfig;
