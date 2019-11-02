import React, { Component } from 'react';
import io from 'socket.io-client';
import { withStyles } from '@material-ui/core';

const styles = theme => ({
  root: {},
  grid: {
    display: 'flex',
    'flex-direction': 'row',
    'justify-content': 'center',
    'align-items': 'baseline',
    'width': '100%',
    'box-sizing': 'border-box',
    'flex-wrap': 'wrap',
    padding: '1em',

    '& > div': {
      width: '20px',
      'height': '20px',
    },
  },
});

class Core extends Component {
  constructor(props) {
    super(props);

    this.state = {
      socket: io(':5000'),
      core_state: [],
    }
  }

  componentDidMount(){
    const { socket } = this.state;

    socket.on('connect', () => {
      console.log("Connected!");
    });
    
    socket.on('connection', core => {
      this.setState({ core_state: core });
    });

    socket.on('disconnect', () => {
      // TODO: add a boundary to check for disconnect and render a "disconnected" error
    });

    socket.on('core_state', updates => {
      console.log(updates);
      var core = JSON.parse(JSON.stringify(this.state.core_state));
      updates.forEach(update => {
        core[update[0]] = update[1];
      });
      this.setState({ core_state: core });
    });
  }

  componentWillUnmount() {
    const { socket } = this.state;
    console.log('Leaving');
  }

  render() {
    const { classes } = this.props;
    const { core_state } = this.state;

    return (
      <div className={classes.grid}>
          {core_state.map((data, idx) =>
            <div key={idx} className="box" style={{backgroundColor: "#" + (255 - data).toString(16).repeat(3)}}>
            </div>  
          )}
        </div>
    );
  }
}


export default withStyles(styles)(Core);