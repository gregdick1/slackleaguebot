import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { LeagueContext } from "../contexts/League"
import DatePicker from "react-multi-date-picker"
import './NewSeason.css'

function NewSeason({callback}) {

    const [ leagueState, dispatch ] = React.useContext(LeagueContext)

    const [startDate, setStartDate] = useState('')
    const [weeksToSkip, setWeeksToSkip] = useState([])
    const [setsNeeded, setSetsNeeded] = useState(0)

    const [groupSizeWarning, setGroupSizeWarning] = useState(false)
    const [shouldIncludeByes, setShouldIncludeByes] = useState(false)
    const [shouldPlayAllSets, setShouldPlayAllSets] = useState(false)

    useEffect(() => {
      const fetchData = async () => {
        const players = (await axios.get('/get-all-players')).data
        const groupSizes = new Map()
        for(var p of players) {
          if (p.grouping === '') continue
          if (![...groupSizes.keys()].includes(p.grouping)) {
            groupSizes.set(p.grouping, 0)
          }
          groupSizes.set(p.grouping, groupSizes.get(p.grouping)+1)
        }
        var uniqueGroupSizes = [... new Set([...groupSizes.values()])]
        var maxGroupSize = Math.max(...uniqueGroupSizes)
        var minGroupSize = Math.min(...uniqueGroupSizes)
        if (maxGroupSize - minGroupSize > 1) {
          setGroupSizeWarning(true)
        }
        if (maxGroupSize % 2 === 0) {
          setShouldIncludeByes(true)
        }
      }

      fetchData().catch(console.error);
    }, []);

    const createSeason = () => {
      const updateServer = async () => {
        await axios.post(`create-season`,
            {
                leagueName: leagueState.selectedLeague,
                startDate: new Date(startDate.year, startDate.month-1, startDate.day).toISOString(),
                skipWeeks: weeksToSkip.map(v => new Date(v.year, v.month-1, v.day).toISOString()),
                setsNeeded: setsNeeded,
                playAllSets: shouldPlayAllSets,
                includeByes: shouldIncludeByes
            });

        dispatch({ type: "need_to_check_for_commands", checkForCommandsToRun:true})
        document.getElementById('new-season-close-btn').click()
        callback()
      }
      updateServer().catch(console.error);
    }

    return (
          <div class="modal-dialog modal-dialog-centered" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="create-season-title modal-title" id="modalLabel">Create New Season</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>
              <div class="modal-body">
                 {groupSizeWarning &&
                     <div className="group-size-warning">
                     Your group sizes currently vary by more than 1. This will result in an uneven season where some groups will have more weeks than others. It is highly recommended to choose an ideal group size that is an even number (e.g. 8) and then either allow groups to be one less or one more, but not both.
                     </div>
                 }
                 <div className="new-season-form">
                    <div className="new-season-field">
                        <label>Start Date:</label>
                        <DatePicker
                          value={startDate}
                          onChange={setStartDate}
                        />
                        <div className="field-context">This is typically the Monday of the first week you want matches played. All following matches will be assigned to the same day of the week, one week after another.</div>
                    </div>
                    <div className="new-season-field">
                        <label>Weeks to skip:</label>
                        <DatePicker
                          multiple
                          value={weeksToSkip}
                          onChange={setWeeksToSkip}
                        />
                        <div className="field-context">If there are weeks you don't want matches scheduled, add them here. It should be the same day of the week as the start date.</div>
                    </div>
                    <div className="new-season-field">
                        <label>Play All Sets</label>
                        <input type="checkbox" checked={shouldPlayAllSets} onChange={(e) => setShouldPlayAllSets(e.target.checked)}/>
                        <div className="field-context">If checked, all sets in a match must be played.  If unchecked, the match will be played as a "best-of" series.</div>
                    </div>
                    {shouldPlayAllSets && <div className="new-season-field">
                        <label>Total Sets to Play</label>
                        <input id="totalSets" name="totalSets" type="number" onChange={(e) => setSetsNeeded(e.target.value)}/>
                        <div className="field-context">Total sets to play if not doing a best-of series</div>
                    </div>}
                    {!shouldPlayAllSets && <div className="new-season-field">
                        <label>First to</label>
                        <input id="setsNeeded" name="setsNeeded" type="number" onChange={(e) => setSetsNeeded(e.target.value)} />
                        <span>wins</span>
                        <div className="field-context">The number of sets/games a person needs to win to win the match. If there are no sets/games and it's a simple win or lose, just put 1.</div>
                    </div>}
                    <div className="new-season-field">
                        <label>Include Byes:</label>
                        <input type="checkbox" checked={shouldIncludeByes} onChange={(e) => setShouldIncludeByes(e.target.checked)} />
                        <div className="field-context">This is only useful if you have odd # groups that are smaller than even # groups. This introduces "bye" matches so that the odd # groups have the same number of weeks as the even # groups. This should already be set intelligently based on your current group sizes.</div>
                    </div>
                </div>
              </div >
              <div class="modal-footer">
                <button id="new-season-close-btn" type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onClick={createSeason}>Create Season</button>
              </div>
            </div>
          </div>
    );
}

export default NewSeason;
