import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";

import { LeagueContext } from "../contexts/League"
import groupBy from '../helpers.js'
import PlayerGroup from './PlayerGroup';
import Spinner from "../Components/Spinner"
import DbUpdater from "../Components/DbUpdater"

import './PlayerBoard2.css'

function PlayerBoard2() {

    const [seasonPlayers, setSeasonPlayers] = useState([])
    const [season, setSeason] = useState(-1)
    const [seasons, setSeasons] = useState([])
    const [orderedActivePlayersAndMarkers, setOrderedActivePlayersAndMarkers] = useState([])
    const [inactivePlayers, setInactivePlayers] = useState([])
    const [deactivatedSlackIds, setDeactivatedSlackIds] = useState([])
    const [deactivating, setDeactivating] = useState(false)

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
            group_players.sort((a,b) => a.order_idx > b.order_idx ? 1 : ((a.order_idx < b.order_idx) ? -1 : 0))
            orderedActivePlayersAndMarkers.push({name:group_name+" "+group_players.length+" players", slack_id:group_name});
            orderedActivePlayersAndMarkers.push(...group_players)
        }
        setOrderedActivePlayersAndMarkers(orderedActivePlayersAndMarkers)
      }

      fetchData().catch(console.error);
    }, [leagueState.selectedLeague, season, reload]);

    const handleGetDeactivated = () => {
      setDeactivating(true)
      const updateServer = async () => {
        let response = await axios.get(`get-deactivated-players`, { params: { leagueName: leagueState.selectedLeague } });
        setDeactivatedSlackIds(response.data)
        setDeactivating(false)
        setReload(true)
      }

      updateServer().catch(console.error);
    }

    const addPlayer = (playerName) => {
        setOrderedActivePlayersAndMarkers([...orderedActivePlayersAndMarkers, {slack_id: 'waiting', name:playerName}])
        let groups = orderedActivePlayersAndMarkers.filter(p => p.slack_id.length === 1).map(p => p.slack_id)
        let bottomGroup = groups[groups.length-1]


        const updateServer = async () => {
          let response = await axios.post(`add-player`, { leagueName: leagueState.selectedLeague, playerName: playerName, grouping: bottomGroup });
          if (response.data['success']) {
            dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
          } else {
            alert("Adding Player failed: "+response.data['message'])
          }
          setReload(true)
        }

        updateServer().catch(console.error);
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
        // Dropped in same spot it was
        if (result.destination.index === result.source.index && result.destination.droppableId === result.source.droppableId) {
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
          let movedPlayer = result.source.droppableId == 'active' ?
            orderedActivePlayersAndMarkers.filter(p => p.slack_id === result.draggableId)[0] :
            inactivePlayers.filter(p => p.slack_id === result.draggableId)[0]

          let playersAndGroups = [...orderedActivePlayersAndMarkers]
          let iPlayers = [...inactivePlayers]

          //If we moved down, then our thing ends up _below_ the thing at destination
          //If we moved up, then our thing ends up _above_ the thing at destination
          const movedDown = result.source.index < result.destination.index

          //Read source and destination groups before modifying list
          let currentGroup = ''
          let sourceGroup = ''
          let destinationGroup = ''
          for (var [i, slack_id] of playersAndGroups.map(p => p.slack_id).entries()) {
            if (movedDown && slack_id.length == 1) currentGroup = slack_id
            if (i == result.source.index) sourceGroup = currentGroup;
            if (i == result.destination.index) destinationGroup = currentGroup;
            if (!movedDown && slack_id.length == 1) currentGroup = slack_id
          }

          let newSpot = result.destination.index + (movedDown ? 1 : 0)
          if (result.source.droppableId == 'active') {
            if (movedDown) { //moved a player down the list'
              playersAndGroups.splice(newSpot, 0, movedPlayer) //add player in the new position
              playersAndGroups.splice(result.source.index, 1) //remove player from the original spot
            } else { //moved a player up the list, need to remove first
              playersAndGroups.splice(result.source.index, 1)
              playersAndGroups.splice(newSpot, 0, movedPlayer)
            }
          } else { //Moved a player from inactive
            playersAndGroups.splice(newSpot, 0, movedPlayer)
            iPlayers.splice(result.source.index, 1)
            sourceGroup = destinationGroup
          }
          let groups = {}
          currentGroup = ''
          for (var [i, slack_id] of playersAndGroups.map(p => p.slack_id).entries()) {
            if (slack_id.length == 1) { //it's a group
              currentGroup = slack_id
              groups[currentGroup] = []
            } else {
              groups[currentGroup].push(slack_id)
            }
          }

          let playersAndGroupsIds = playersAndGroups.map(p => p.slack_id)
          let groupAfter = String.fromCharCode(sourceGroup.charCodeAt(0) + 1)
          let sourceGroupPlayers = playersAndGroupsIds.indexOf(groupAfter) > -1 ?
            playersAndGroupsIds.slice(playersAndGroupsIds.indexOf(sourceGroup)+1, playersAndGroupsIds.indexOf(groupAfter)) :
            playersAndGroupsIds.slice(playersAndGroupsIds.indexOf(sourceGroup)+1, playersAndGroupsIds.length)

          let destinationGroupPlayers = []
          if (destinationGroup !== sourceGroup) {
            groupAfter = String.fromCharCode(destinationGroup.charCodeAt(0) + 1)
            destinationGroupPlayers = playersAndGroupsIds.indexOf(groupAfter) > -1 ?
              playersAndGroupsIds.slice(playersAndGroupsIds.indexOf(destinationGroup)+1, playersAndGroupsIds.indexOf(groupAfter)) :
              playersAndGroupsIds.slice(playersAndGroupsIds.indexOf(destinationGroup)+1, playersAndGroupsIds.length)
          }

          const updateServer = async () => {
            setOrderedActivePlayersAndMarkers(playersAndGroups)
            setInactivePlayers(iPlayers)
            await axios.post(`update-player-grouping-and-orders`, { leagueName: leagueState.selectedLeague, players: sourceGroupPlayers, grouping: sourceGroup });
            if (destinationGroup !== sourceGroup) {
              await axios.post(`update-player-grouping-and-orders`, { leagueName: leagueState.selectedLeague, players: destinationGroupPlayers, grouping: destinationGroup });
            }
            setReload(true)
            dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
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

    const promotedOrDemoted = (slack_id) => {
      let currentGroup = ''
      for (var id of orderedActivePlayersAndMarkers.map(p => p.slack_id)) {
        if (id.length === 1) currentGroup = id
        if (id === slack_id) break;
      }
      let lastSeason = seasonPlayers.filter(p => p.slack_id === slack_id)
      if (lastSeason.length > 0) {
        let lastSeasonGroup = lastSeason[0].group
        if (lastSeasonGroup < currentGroup) return 'demoted'
        if (lastSeasonGroup > currentGroup) return 'promoted'
      }
      return ''
    }

    const resolveClass = (slack_id) => {
      if (slack_id.length === 1) return 'group-marker'
      let cls = ''
      if (deactivatedSlackIds.indexOf(slack_id) > -1) cls += ' deactivated-player'
      if (slack_id === 'waiting') cls += ' pending-player'
      let pod = promotedOrDemoted(slack_id)
      if (pod.length > 0) cls += ' '+pod+'-player'
      if (cls === '')
        return 'player-in-group'
      return cls
    }

    if (leagueState.needDbUpdate)
        return <DbUpdater />
    return (
      <div className="groups-container">
        <div id='playerboard-legend'>
          <button
            id='get-deactivated-btn'
            className="btn btn-primary"
            disabled={deactivating}
            onClick={handleGetDeactivated}
            title="Check slack to see who's been deactivated and mark the players">
            { deactivating &&
              <Spinner size={20} />
            }
            <span>Mark Deactivated</span>
          </button>
          <div className="group-wrapper">
            <div className="group-title"><span>Color Key</span></div>
            <div className="deactivated-player">Deactivated From Slack</div>
            <div className="promoted-player">Promoted Player</div>
            <div className="demoted-player">Relegated Player</div>
            <div className="pending-player">Pending Slack ID Retrieval</div>
          </div>
        </div>

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
                        <div className={resolveClass(player.slack_id)} ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} >
                            <div>{player.name}</div>
                        </div>
                    )}
                </Draggable>
                ))}
                { provided.placeholder }

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
                <div className="add-group-marker" onClick={addGroup}>
                  <span>Add Group..</span>
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
                        <div className='player-in-group' ref={provided.innerRef} {...provided.draggableProps} {...provided.dragHandleProps} >
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
