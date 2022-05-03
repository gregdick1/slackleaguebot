import React from "react"
import { reducer, initialState } from "./reducer"

export const LeagueContext = React.createContext({
  state: initialState,
  dispatch: () => null
})

export const LeagueProvider = ({ children }) => {
  const [state, dispatch] = React.useReducer(reducer, initialState)

  return (
    <LeagueContext.Provider value={[ state, dispatch ]}>
    	{ children }
    </LeagueContext.Provider>
  )
}