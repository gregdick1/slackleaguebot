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

    const handleSubmit = async (e) => {
        e.preventDefault()
        // TODO: Add check to ensure all keys have values
        console.log({...state})
        await axios.post('/set-config-value', { ...state })

        alert("success")
    }

    return (
      <div id="main-content" className="main-content">
        <form className="form-group col-4">
            <label>League Name</label>
            <input class="form-control" name="leagueName" type="text" value={state.leagueName} onChange={handleChange} />

            <label>Slack API Key</label>
            <input class="form-control" name="APIKey" type="text" value={state.APIKey} onChange={handleChange}/>

            <label>Slack Bot User ID</label>
            <input class="form-control" name="botUserID" type="text" value={state.botUserID} onChange={handleChange}/>

            <label>Slack Channel ID</label>
            <input class="form-control" name="channelID" type="text" value={state.channelID} onChange={handleChange}/>

            <label>Commissioner Slack ID</label>
            <input class="form-control" name="commissionerID" type="text" value={state.commissionerID} onChange={handleChange}/>

            <label>First to Number of Sets</label>
            <input class="form-control" name="numOfSets" type="number" value={state.numOfSets} onChange={handleChange} />
            <button id="submit-button" className="btn btn-primary btn-lg" onClick={handleSubmit}>Submit</button>
        </form>
        Configuration!
      </div>
    );
}

export default Configuration;
