import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

import { LeagueContext } from "../contexts/League"
import groupBy from '../helpers.js'
import PlayerGroup from './PlayerGroup';

import './PlayerBoard2.css'

function PlayerBoard2() {

    const [seasonPlayers, setSeasonPlayers] = useState([])
    const [season, setSeason] = useState(-1)
    const [seasons, setSeasons] = useState([])
    const [orderedActivePlayersAndMarkers, setOrderedActivePlayersAndMarkers] = useState([])
    const [inactivePlayers, setInactivePlayers] = useState([])

    const [addingPlayer, setAddingPlayer] = useState(false)
    const [addPlayerName, setAddPlayerName] = useState("")

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
        let seasonPlayers = (await axios.get(`get-players-from-season`,
            { params: { leagueName: leagueState.selectedLeague, season: seasonToLoad } })).data
        let allPlayers = (await axios.get(`get-all-players`, { params: { leagueName: leagueState.selectedLeague } })).data

        setSeasonPlayers(seasonPlayers)

        const inactivePlayers = allPlayers.filter((p) => p.grouping === '');
        inactivePlayers.sort((a,b) => a.name > b.name ? 1 : ((a.name < b.name) ? -1 : 0))
        setInactivePlayers(inactivePlayers)

        let activePlayers = allPlayers.filter((p) => p.grouping !== '');
        activePlayers.sort((a,b) => a.grouping > b.grouping ? 1 : ((a.grouping < b.grouping) ? -1 : 0))
        const orderedActivePlayersAndMarkers = []
        for (var group of Object.entries(groupBy(activePlayers, 'grouping'))) {
            const group_name = group[0]
            const group_players = group[1]
            group_players.sort((a,b) => a.name > b.name ? 1 : ((a.name < b.name) ? -1 : 0))
            orderedActivePlayersAndMarkers.push({name:group_name+" "+group_players.length+" players", slack_id:group_name});
            orderedActivePlayersAndMarkers.push(...group_players)
        }
        setOrderedActivePlayersAndMarkers(orderedActivePlayersAndMarkers)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, season, reload]);

    const addPlayer = (playerName) => {
        console.log('Implement me')
      }

    const addGroup = () => {
      let lastGroup = ''
      for (const [index, playerOrMarker] of orderedActivePlayersAndMarkers.entries()) {
        if (playerOrMarker.slack_id.length === 1) lastGroup = playerOrMarker.slack_id
      }
      let newGroup = String.fromCharCode(lastGroup.charCodeAt(0) + 1) //Please don't go past Z...
      let o = [...orderedActivePlayersAndMarkers]
      o.push({name:newGroup+" 0 players", slack_id:newGroup});
      setOrderedActivePlayersAndMarkers(o)
    }

    const onDragEnd = (result) => {
        console.log(result)
        // dropped outside the list
        if (!result.destination) {
          return;
        }
        if (result.destination.droppableId === 'inactive' &&
            (result.source.droppableId === 'inactive' || result.draggableId.length === 1) ) {
          return;
        }
        // Can't move the A group marker
        if (result.draggableId === 'A') {
          return;
        }
        // Can't move a player above A
        if (result.destination.droppableId === 'active' && result.destination.index === 0) {
          return;
        }

        //setting a player inactive
        if (result.destination.droppableId === 'inactive') {
          const updateServer = async () => {
            await axios.post(`inactivate-player`, { leagueName: leagueState.selectedLeague, playerId: result.draggableId });
            dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
            setReload(true)
          }

          updateServer().catch(console.error);
          return;
        }

        //Moved a person
        if (result.draggableId.length > 1) {
          let lastGroup = ''
          for (const [index, playerOrMarker] of orderedActivePlayersAndMarkers.entries()) {
            //if both things are true, we moved a player on a group marker
            if (playerOrMarker.slack_id.length === 1 && index === result.destination.index) {
              //if the destination index is lower, we moved the player up and should not read the group
              if (result.destination.index < result.source.index) break;
            }
            if (playerOrMarker.slack_id.length === 1) lastGroup = playerOrMarker.slack_id
            if (index === result.destination.index) break;
          }
          const updateServer = async () => {
            await axios.post(`update-player-grouping`, { leagueName: leagueState.selectedLeague, playerId: result.draggableId, grouping: lastGroup });
            dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
            setReload(true)
          }

          updateServer().catch(console.error);
          return;
        } else { //Moved group marker

        }

        console.log('Implement me')
    }

    const onReturn = (e) => {
        if(e.keyCode == 13){
            addPlayer(e.target.value)
            setAddPlayerName("")
            setAddingPlayer(false)
        }
    }

    const orderedLastSeasonPlayers = []
    for (var group of Object.entries(groupBy(seasonPlayers, 'group'))) {
        const group_name = group[0]
        const group_players = group[1]
        orderedLastSeasonPlayers.push(
          <div className='group-marker'>{group_name}</div>
        );
        for (var player of group_players) {
          orderedLastSeasonPlayers.push(
            <div className='player-in-group'>{player.name} {player.games_won}-{player.games_lost} ({player.sets_won}-{player.sets_lost})</div>
          )
        }
    }



    return (
      <div className="groups-container">

        <div className="group-wrapper">
          <div className="group-title">
            <span>Players from season: </span>
            <select name='selectedSeason' value={season} onChange={(e) => setSeason(e.target.value)}>
              {seasons.map((s) => (
                  <option value={s}>{s}</option>
                ))}
            </select>
          </div>
          {orderedLastSeasonPlayers}
        </div>
        <DragDropContext onDragEnd={onDragEnd}>
          <Droppable droppableId='active'>
            {(provided, snapshot) => (
            <div {...provided.droppableProps} ref={provided.innerRef} className="group-wrapper" >
              <div className="group-title">Active Players</div>
                {orderedActivePlayersAndMarkers && orderedActivePlayersAndMarkers.map((player, index) => (
                <Draggable key={player.slack_id} draggableId={player.slack_id} index={index}>
                    {(provided, snapshot) => (
                        <div className={player.slack_id.length===1 ? 'group-marker' : 'player-in-group'} ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} >
                            <div>{player.name}</div>
                        </div>
                    )}
                </Draggable>
                ))}
                { provided.placeholder }
                <div className="add-group-marker" onClick={addGroup}>
                  <span>Add Group..</span>
                </div>
                <div className="add-player" onClick={() => setAddingPlayer(true)}>
                    {
                        addingPlayer ?
                            <input type="text"
                              onBlur={() => setAddingPlayer(false)}
                              onKeyDown={onReturn}
                              value={addPlayerName}
                              onChange={(e) => setAddPlayerName(e.target.value)}
                              autoFocus/> :
                            <span>Add Player..</span>
                    }
                </div>
            </div>
            )}
          </Droppable>
          <Droppable droppableId='inactive'>
            {(provided, snapshot) => (
            <div {...provided.droppableProps} ref={provided.innerRef} className="group-wrapper" >
              <div className="group-title">Inactive Players</div>
                {inactivePlayers && inactivePlayers.map((player, index) => (
                <Draggable key={player.slack_id} draggableId={player.slack_id} index={index} className="player-box">
                    {(provided, snapshot) => (
                        <div className="player-in-group" ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} >
                            <div>{player.name}</div>
                        </div>
                    )}
                </Draggable>
                ))}
                { provided.placeholder }
            </div>
            )}
          </Droppable>
        </DragDropContext>
      </div>
    );
}

export default PlayerBoard2;
