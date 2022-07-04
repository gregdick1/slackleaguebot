import React from 'react'
import { InfoCircle } from 'react-bootstrap-icons';
import './ToolTip.css'

function ToolTip({size, width, text}) {
    const style = {
        width: width,
        marginLeft: -width/2,
    }
    return (
      <div className="info-tooltip">
        <InfoCircle size={size} />
        <span className="info-tooltip-text" style={style}>{text}</span>
      </div>
    );
}

export default ToolTip;
