import React, { Component } from 'react';
import io from 'socket.io-client';
import { withStyles } from '@material-ui/core'

const styles = theme => ({
  root: {
    display: 'flex',
    'flex-direction': 'column',
    'align-items': 'baseline',
    'justify-content': 'center',
  },
  title: {
    width: '100%',
    display: 'flex',
    'justify-content': 'center',
    'font-size': "32px",
    
    'padding': '1em',
  },
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
      width: '15px',
      'height': '20px',
    },
  },
});


class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      socket: io(':5000'),
      state: [],
    }
  }

  componentDidMount(){
    const { socket } = this.state;

    socket.on('connect', () => {
      console.log("Connected!");
    });

    socket.on('disconnect', () => {
      // TODO: add a boundary to check for disconnect and render a "disconnected" error
    });

    socket.on('state', data => {
      this.setState({ state: data });
    });
  }

  render() {
    const { classes } = this.props;

    const { state } = this.state;

    return(
      <div className={classes.root}>
        <div className={classes.title}>
          Yeet Wars
        </div>
        <div className={classes.grid}>
          {state.map((data, idx) =>
            <div key={idx}>
              {data}
            </div>  
          )}
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(App);
