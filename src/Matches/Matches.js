import React, { Component } from 'react'
import axios from 'axios'

import './Matches.css'

class Matches extends Component {
    constructor(props) {
        super(props);
        this.state = {
            matches: []
        }
    }

    async componentDidMount() {
        const matches = await axios.get('/get-current-matches');

        this.setState({
            matches
        })
    }

    render() {
        console.log(this.state.matches)
      return (
      <div id="main-content" className="main-content">
        Matches!
      </div>
    );
    }
}

export default Matches;
