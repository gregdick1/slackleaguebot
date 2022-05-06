import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"

import './LastRefresh.css'

function LastRefresh() {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [now, setNow] =  useState(new Date())

    useEffect(() => {
      const interval = setInterval(() => {
        setNow(new Date());
      }, 1000);

      return () => {
        clearInterval(interval);
      };
    }, [now]);

    const d = new Date(leagueState.lastRefreshed)
    const prettyTime = (timeInMs) => {
        let toReturn = ''
        if (timeInMs > 1000*60*60) {
            let hrs = Math.floor(timeInMs/(1000*60*60))
            toReturn += hrs + 'hrs '
            timeInMs -= hrs*(1000*60*60)
        }
        if (timeInMs > 1000*60 || toReturn.length > 0) {
            let min = Math.floor(timeInMs/(1000*60))
            toReturn += min + 'm '
            timeInMs -= min*(1000*60)
        }
        if (timeInMs > 1000 || toReturn.length > 0) {
            toReturn += Math.floor(timeInMs/1000) + 's'
        }
        return toReturn
    }
    return (
      <span>
          <label>Last Refresh: </label>
          <span>{prettyTime(now.getTime() - d.getTime())}</span>
      </span>
    );
}

export default LastRefresh;
