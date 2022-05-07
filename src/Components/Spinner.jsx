import React from 'react'

import './Spinner.css'

function Spinner({size}) {
    const style = {
        width: size,
        height: size,
        border: (size/4)+"px solid #f3f3f3",
        borderTop: (size/4)+"px solid transparent"
    }
    return (
      <div className="spinner-container">
        <div className="loading-spinner" style={style}>
        </div>
      </div>
    );
}

export default Spinner;
