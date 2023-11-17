import React, { useState, useEffect } from 'react'
import { Pencil, Check, X } from 'react-bootstrap-icons';
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import DbUpdater from "../Components/DbUpdater"
import EdiText from 'react-editext';
import './Configuration.css'

function Configuration() {

    const blankConfigs = {
        LOG_PATH: 'log.txt',
        BOT_NAME: '@bot',
        SCORE_EXAMPLE: '3-2'
    }
    const [state, setState] = useState({
        leagueConfigs: {...blankConfigs}
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

    const handleCheck = async ({target: { name, checked }}) => {
        var val = checked ? "TRUE" : "FALSE"
        var leagueConfigs = {...state.leagueConfigs, [name]: val}
        setState({
          ...state,
          leagueConfigs
        })
        const response = await axios.post('set-league-config', {
                selectedLeague: leagueState.selectedLeague,
                configKey: name,
                configValue: val
            });
        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
    }


    const checkbox = (label, config, nullIsTrue) => {
      var checked = "checked"
      if (state.leagueConfigs[config] === 'FALSE' || (state.leagueConfigs[config] !== 'TRUE' && !nullIsTrue)) {
        checked = ""
      }
      return (
      <div className="inline-editor">
        <label>{label}:</label>
        <input type="checkbox"
          id={config}
          name={config}
          onChange={handleCheck}
          checked={checked}
        />
      </div>
      );
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
          inputProps={{ name: config, style: { padding: 0 } }}
          containerProps={{ style: { display: 'inline-block' } }}
          saveButtonContent={<Check size={14} />}
          cancelButtonContent={<X size={14} />}
          editButtonContent={<Pencil size={14} />}
          saveButtonClassName="btn inline-btn inline-save-btn"
          editButtonClassName="btn inline-btn inline-edit-btn"
          cancelButtonClassName="btn inline-btn inline-cancel-btn"
          viewContainerClassName="inline-editor-view"
        />
      </div>
      );
    }

    const editExisting = leagueState.leagues.length > 0;
    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div id="main-content" className="main-content">
        <div className="config-content">
          <div className="tab-header">
            <label>Admin Configuration for League: {leagueState.selectedLeague}</label>
          </div>
            { !editExisting &&
                <div>Please select or create a League first</div>
            }
            <div className="config-area">
              <div className="config-box">
                <label>Slack Configs</label>
                { editExisting && editor('Slack API Key', 'SLACK_API_KEY') }
                { editExisting && editor('Slack App Key', 'SLACK_APP_KEY') }
                { editExisting && editor('Competition Channel Slack ID', 'COMPETITION_CHANNEL_SLACK_ID') }
                { editExisting && editor('Bot Slack User ID', 'BOT_SLACK_USER_ID') }
                { editExisting && editor('Commissioner Slack ID', 'COMMISSIONER_SLACK_ID') }
              </div>
              <div className="config-box">
                <label>Help Configs</label>
                { editExisting && editor('Bot Name', 'BOT_NAME') }
                { editExisting && editor('Example Score', 'SCORE_EXAMPLE') }
              </div>
              <div className="config-box">
                <label>Enable Commands</label>
                { editExisting && checkbox('Group Analysis', 'ENABLE_COMMAND_GROUP_ANALYSIS', true) }
                { editExisting && checkbox('Leaderboard', 'ENABLE_COMMAND_LEADERBOARD', true) }
                { editExisting && checkbox('Matchup History', 'ENABLE_COMMAND_MATCHUP_HISTORY', true) }
                { editExisting && checkbox('User Stats', 'ENABLE_COMMAND_USER_STATS', true) }
                { editExisting && checkbox('Week Matches', 'ENABLE_COMMAND_WEEK_MATCHES', true) }
              </div>
              <div className="config-box">
                <label>Other Configs</label>
                { editExisting && editor('Log Path', 'LOG_PATH') }
                { editExisting && checkbox('Block New Scores', 'BLOCK_NEW_SCORES', false)}
                { editExisting && checkbox('Message Commissioner On Score Entry', 'MESSAGE_COMMISSIONER_ON_SUCCESS', false)}
              </div>
              <div className="config-box">
                <label>Message Configs</label>
                { editExisting && editor('Match Message', 'MATCH_MESSAGE')}
                { editExisting && editor('Reminder Message', 'REMINDER_MESSAGE')}
              </div>
            </div>
        </div>
      </div>
    );
}

export default Configuration;
