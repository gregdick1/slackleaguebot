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
    case "need_to_check_for_commands":
      return {
        ...state,
        checkForCommandsToRun: action.checkForCommandsToRun
      }
    case "need_db_update":
      return {
        ...state,
        needDbUpdate: action.needDbUpdate
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
  hasDeployed: false,
  checkForCommandsToRun: false,
  needDbUpdate: false
}