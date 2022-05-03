export const reducer = (state, action) => {
  switch (action.type) {
    case "league_changed":
      return {
        ...state,
        selectedLeague: action.selectedLeague,
        leagues: action.leagues
      }

    default:
      return state
  }
}

export const initialState = {
  selectedLeague: "",
  leagues: []
}