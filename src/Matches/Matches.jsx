import React, { useState, useEffect } from 'react'
import { GripHorizontal } from 'react-bootstrap-icons';
import axios from 'axios'

import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import { LeagueContext } from "../contexts/League"
import DbUpdater from "../Components/DbUpdater"
import MatchDisplay from './MatchDisplay'
import MatchEditor from './MatchEditor'
import './Matches.css'

function Matches() {
    const [seasonMatches, setSeasonMatches] = useState({})
    const [season, setSeason] = useState(-1)
    const [seasons, setSeasons] = useState([])
    const [allPlayers, setAllPlayers] = useState([])

    const [reload, setReload] = useState(false)

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    useEffect(() => {
      const fetchData = async () => {
        setReload(false)
        if (!leagueState.selectedLeague) return

        let seasons = (await axios.get('get-all-seasons', { params: { leagueName: leagueState.selectedLeague } })).data
        setSeasons(seasons)
        let seasonToLoad = season
        if (seasonToLoad === -1) {
          seasonToLoad = seasons[seasons.length-1]
          setSeason(seasonToLoad)
        }
        const players = (await axios.get('/get-all-players')).data
        setAllPlayers(players)
        let matches = (await axios.get('get-matches-for-season', { params: { leagueName: leagueState.selectedLeague, season: seasonToLoad}})).data
        setSeasonMatches(matches)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, leagueState.lastRefreshed, season, reload]);


    const onDragEnd = (result) => {
        console.log(result)
        // dropped outside the list
        if (!result.destination) {
          return;
        }
    }

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div className="matches-container">
        <div className="matches-controls">
          <div className="season-control">
            <span>Matches from season: </span>
            <select name='selectedSeason' value={season} onChange={(e) => setSeason(e.target.value)}>
              {seasons.map((s) => (
                  <option value={s}>{s}</option>
                ))}
            </select>
          </div>
        </div>
        <DragDropContext onDragEnd={onDragEnd}>
        {Object.entries(seasonMatches).map(([group, groupMatches]) => (
          <Droppable droppableId={group} direction="horizontal">
            {(provided, snapshot) => (
              <div {...provided.droppableProps} ref={provided.innerRef} className="group-row">
                {Object.entries(groupMatches).map(([week, weekMatches], index) => (
                  <Draggable key={group+week} draggableId={group+week} index={index}>
                    {(provided, snapshot) => (
                      <div className="group-week" ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps}>
                        <div className="week-title">
                          <span>{week}</span>
                          <span className="week-grip"><GripHorizontal size={24} style={{color: 'grey'}} /></span>
                        </div>
                        {weekMatches.map(match => (
                          <>
                            <div className="match-box" data-toggle="modal" data-target={`#modal-${match.id}`}>
                              <MatchDisplay match={match} allPlayers={allPlayers} />
                            </div>

                            <div class="modal show" id={`modal-${match.id}`} tabIndex="-1" role="dialog" aria-labelledBy="modalLabel" aria-hidden="true">
                              <div class="modal-dialog modal-dialog-centered" role="document">
                                <div class="modal-content">
                                  <div class="modal-header">
                                    <h5 class="modal-title" id="modalLabel">Update Match</h5>
                                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                      <span aria-hidden="true">&times;</span>
                                    </button>
                                  </div>
                                  <div class="modal-body">
                                      <MatchEditor match={match} allPlayers={allPlayers} />
                                  </div >
                                  <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </>
                        ))}
                      </div>
                    )}
                  </Draggable>
                ))}
              </div>
            )}
          </Droppable>
        ))}
        </DragDropContext>
      </div>
    );
}

export default Matches;
