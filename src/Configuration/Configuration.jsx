import React, { useState, useEffect } from 'react'
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import EdiText from 'react-editext';
import './Configuration.css'

function Configuration() {
    const [state, setState] = useState({
        leagueConfigs: {}
    })

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {
        // get the data from the api
        var configsResponse = await axios.get('get-league-configs', { params: { leagueName: leagueState.selectedLeague } })
        var leagueConfigs = configsResponse.data;
        setState({
          ...state,
          leagueConfigs
        });
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.lastRefreshed]);

    const handleSave = async (val, inputProps) => {
        var leagueConfigs = {...state.leagueConfigs, [inputProps.name]: val}
        setState({
          ...state,
          leagueConfigs
        })
        const response = await axios.post('set-league-config', {
                selectedLeague: leagueState.selectedLeague,
                configKey: inputProps.name,
                configValue: val
            });
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
    }

    const editor = (label, config) => {
      return (
      <div className="inline-editor">
        <label>{label}:</label>
        <EdiText
          className="editext-editor"
          type="text"
          value={state.leagueConfigs[config]}
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
        { !editExisting &&
            <div>Please select or create a League first</div>
        }
        { editExisting && editor('Slack API Key', 'SLACK_API_KEY') }
        { editExisting && editor('Competition Channel Slack ID', 'COMPETITION_CHANNEL_SLACK_ID') }
        { editExisting && editor('Bot Slack User ID', 'BOT_SLACK_USER_ID') }
        { editExisting && editor('Commissioner Slack ID', 'COMMISSIONER_SLACK_ID') }
      </div>
    );
}

export default Configuration;
