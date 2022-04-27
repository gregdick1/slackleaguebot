import React, { useState } from 'react'
import axios from 'axios'

import './Configuration.css'

function Configuration() {
    const [state, setState] = useState({
        leagueName: "",
        APIKey: "",
        botUserID: "",
        channelID: "",
        commissionerID: "",
        numOfSets: "",
    })

    const handleChange = (e) => {
        const { value, name } = e.target;
        setState({
            ...state,
            [name]: value
        })
    }

    const handleSubmit = async () => {
        // TODO: Add check to ensure all keys have values
        console.log({...state})
        await axios.post('/set-config-value', { ...state })

        alert("success")
    }

    return (
      <div id="main-content" className="main-content">
        <form id="form-group" className="configuration-form-group">
            <label>League Name</label>
            <input name="leagueName" type="text" value={state.leagueName} onChange={handleChange} />

            <label>Slack API Key</label>
            <input name="APIKey" type="text" value={state.APIKey} onChange={handleChange}/>

            <label>Slack Bot User ID</label>
            <input name="botUserID" type="text" value={state.botUserID} onChange={handleChange}/>

            <label>Slack Channel ID</label>
            <input name="channelID" type="text" value={state.channelID} onChange={handleChange}/>

            <label>Commissioner Slack ID</label>
            <input name="commissionerID" type="text" value={state.commissionerID} onChange={handleChange}/>

            <label>First to Number of Sets</label>
            <input name="numOfSets" type="number" value={state.numOfSets} onChange={handleChange} />

            <button id="submit-button" className="btn btn-primary btn-lg" onClick={handleSubmit}>Submit</button>
        </form>
        Configuration!
      </div>
    );
}

export default Configuration;
