export const reducer = (state, action) => {
  switch (action.type) {
    case "league_changed":
      return {
        ...state,
        selectedLeague: action.selectedLeague,
        leagues: action.leagues
      }
    case "db_refreshed":
      return {
        ...state,
        lastRefreshed: action.lastRefreshed
      }
    case "db_connection_status":
      return {
        ...state,
        hasConnected: action.hasConnected,
        hasDeployed: action.hasDeployed
      }
    default:
      return state
  }
}

export const initialState = {
  selectedLeague: "",
  leagues: [],
  lastRefreshed: null,
  hasConnected: false,
  hasDeployed: false
}