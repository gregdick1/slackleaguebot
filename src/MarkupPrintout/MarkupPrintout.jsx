import React, { useState, useEffect } from 'react'
import axios from 'axios'

import { LeagueContext } from "../contexts/League"
import DbUpdater from "../Components/DbUpdater"
import './MarkupPrintout.css'

function MarkupPrintout() {
    const [ leagueState, dispatch ] = React.useContext(LeagueContext)
    const [ printout, setPrintout ] = useState('')
    const [ seasons, setSeasons ] = useState([])
    const [ season, setSeason ] = useState(-1)
    const [loadedForLeague, setLoadedForLeague] = useState('')
    const [ reload, setReload ] = useState(false)

    useEffect(() => {
      const fetchData = async () => {
        if (loadedForLeague !== leagueState.selectedLeague) {
          //Need to reset our saved season when the league has changed
          setSeason(-1)
          setLoadedForLeague(leagueState.selectedLeague)
        }

        let seasons = (await axios.get('get-all-seasons', { params: { leagueName: leagueState.selectedLeague } })).data
        setSeasons(seasons)
        let seasonToLoad = season
        if (seasonToLoad === -1 && seasons.length > 0) {
          seasonToLoad = seasons[seasons.length-1]
          setSeason(seasonToLoad)
        }
        var response = await axios.get('get-league-markup', { params: { leagueName: leagueState.selectedLeague, season: seasonToLoad } })
        setPrintout(response.data)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.lastRefreshed, reload, season]);

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div id="main-content" className="main-content">
        <div className="markup-controls">
          <span>Season: </span>
          <select name='selectedSeason' value={season} onChange={(e) => setSeason(e.target.value)}>
            {seasons.map((s) => (
                <option value={s}>{s}</option>
              ))}
          </select>
        </div>
        <button onClick={() => setReload(true)}>Refresh</button>
        <textarea disabled="disabled" class="form-control form-rounded" rows="20" value={printout}></textarea>
      </div>
    );
}

export default MarkupPrintout;
