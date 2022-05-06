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
    default:
      return state
  }
}

export const initialState = {
  selectedLeague: "",
  leagues: [],
  lastRefreshed: null
}