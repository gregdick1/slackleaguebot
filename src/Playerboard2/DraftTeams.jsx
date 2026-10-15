import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import { Pencil, Trash } from 'react-bootstrap-icons';
import './DraftTeams.css'

function DraftTeams({ leagueName, onChange, refreshToken = 0 }) {
    const [teams, setTeams] = useState([])
    const [season, setSeason] = useState(null)
    const [players, setPlayers] = useState([])
    const [extraGroups, setExtraGroups] = useState([])
    const [member1, setMember1] = useState('')
    const [member2, setMember2] = useState('')
    const [teamName, setTeamName] = useState('')
    const [teamGroup, setTeamGroup] = useState('A')
    const [reload, setReload] = useState(false)

    useEffect(() => {
      setExtraGroups([])
    }, [leagueName])

    useEffect(() => {
      const fetchData = async () => {
        setReload(false)
        if (!leagueName) return
        const drafts = (await axios.get('get-draft-teams', { params: { leagueName } })).data
        setTeams(drafts.teams)
        setSeason(drafts.season)
        const all = (await axios.get('get-all-players', { params: { leagueName } })).data
        setPlayers(all.filter(p => p.active === 1).sort((a, b) => a.name.localeCompare(b.name)))
      }
      fetchData().catch(console.error)
    }, [leagueName, reload, refreshToken])

    const groups = [...new Set([...teams.map(t => t.grouping), ...extraGroups])].sort()
    const taken = new Set(teams.flatMap(t => [t.member_1, t.member_2]))
    const teamsIn = (g) => teams.filter(t => t.grouping === g).sort((a, b) => a.order_idx - b.order_idx)

    const call = async (url, body) => {
      const response = await axios.post(url, { leagueName, ...body })
      if (response.data.success === false) alert(response.data.message)
      setReload(true)
      if (onChange) onChange()
      return response.data
    }

    const addTeam = async (e) => {
      e.preventDefault()
      const result = await call('add-team', { member1, member2, grouping: teamGroup, name: teamName })
      if (result.success) { setMember1(''); setMember2(''); setTeamName('') }
    }

    const moveTeam = async (teamId, fromGroup, toGroup, toIndex) => {
      const source = teamsIn(fromGroup).map(t => t.team_id).filter(id => id !== teamId)
      const dest = fromGroup === toGroup ? source : teamsIn(toGroup).map(t => t.team_id)
      dest.splice(toIndex === undefined ? dest.length : toIndex, 0, teamId)
      if (fromGroup !== toGroup) await call('update-team-grouping-and-orders', { teamIds: source, grouping: fromGroup })
      await call('update-team-grouping-and-orders', { teamIds: dest, grouping: toGroup })
    }

    const onDragEnd = (result) => {
      if (!result.destination) return
      const { draggableId, source, destination } = result
      if (source.droppableId === destination.droppableId && source.index === destination.index) return
      moveTeam(draggableId, source.droppableId, destination.droppableId, destination.index).catch(console.error)
    }

    const addGroup = () => {
      const last = groups.length ? groups[groups.length - 1] : '@'
      setExtraGroups([...extraGroups, String.fromCharCode(last.charCodeAt(0) + 1)])
    }

    const playerOptions = (exclude) => players.map(p => (
      <option key={p.slack_id} value={p.slack_id} disabled={taken.has(p.slack_id) || p.slack_id === exclude}>{p.name}</option>
    ))

    return (
      <div className="group-wrapper draft-teams">
        <div className="group-title">Season {season} Teams</div>
        <form className="add-team-form" onSubmit={addTeam}>
          <label htmlFor="draft-member-1">Player 1</label>
          <select id="draft-member-1" value={member1} onChange={(e) => setMember1(e.target.value)} required>
            <option value="">Choose…</option>{playerOptions(member2)}
          </select>
          <label htmlFor="draft-member-2">Player 2</label>
          <select id="draft-member-2" value={member2} onChange={(e) => setMember2(e.target.value)} required>
            <option value="">Choose…</option>{playerOptions(member1)}
          </select>
          <label htmlFor="draft-team-name">Team name (optional)</label>
          <input id="draft-team-name" type="text" maxLength={40} value={teamName} onChange={(e) => setTeamName(e.target.value)} />
          <label htmlFor="draft-team-group">Group</label>
          <select id="draft-team-group" value={teamGroup} onChange={(e) => setTeamGroup(e.target.value)}>
            {[...new Set([...groups, 'A'])].sort().map(g => <option key={g} value={g}>{g}</option>)}
          </select>
          <button type="submit" className="btn btn-primary">Add team</button>
          <button type="button" className="btn btn-secondary" onClick={addGroup}>Add group</button>
        </form>
        <DragDropContext onDragEnd={onDragEnd}>
          {groups.map(g => (
            <Droppable droppableId={g} key={g}>
              {(provided) => (
                <div ref={provided.innerRef} {...provided.droppableProps} className="draft-group">
                  <div className="group-marker">Group {g} ({teamsIn(g).length} teams)</div>
                  {teamsIn(g).map((t, index) => (
                    <Draggable key={t.team_id} draggableId={t.team_id} index={index}>
                      {(dragProvided) => (
                        <div className="player-in-group draft-team" ref={dragProvided.innerRef} {...dragProvided.draggableProps} {...dragProvided.dragHandleProps}>
                          <span className="draft-team-label">{t.display_name}</span>
                          <button type="button" className="btn btn-link" aria-label={`Rename ${t.display_name}`}
                                  onClick={() => { const val = window.prompt('Team name (blank for none)', t.name || ''); if (val !== null) call('update-team', { teamId: t.team_id, name: val }) }}>
                            <Pencil size={14} />
                          </button>
                          <label className="sr-only" htmlFor={`group-${t.team_id}`}>Group for {t.display_name}</label>
                          <select id={`group-${t.team_id}`} value={t.grouping} onChange={(e) => moveTeam(t.team_id, t.grouping, e.target.value).catch(console.error)}>
                            {groups.map(o => <option key={o} value={o}>{o}</option>)}
                          </select>
                          <button type="button" className="btn btn-link" aria-label={`Delete ${t.display_name}`}
                                  onClick={() => window.confirm(`Delete ${t.display_name}?`) && call('delete-team', { teamId: t.team_id })}>
                            <Trash size={14} />
                          </button>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          ))}
        </DragDropContext>
      </div>
    )
}

export default DraftTeams;
