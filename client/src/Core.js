import React, { Component } from 'react';
import io from 'socket.io-client';
import { withStyles } from '@material-ui/core';

const styles = theme => ({
  root: {},
  grid: {
    display: 'flex',
    'flex-direction': 'row',
    'justify-content': 'left',
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
      socket: null,
      core_state: [],
      thread_states: {},
      thread_locs: {}
    }
  }

  componentDidMount(){
    const { token } = this.props;

    const socket = io(':5000', {
      query: `token=${token}`,
    });

    if (!socket.connected) { 
      console.log("Bad");
    }

    socket.on('connect', () => {
      console.log("Connected!");
    });

    socket.on('disconnect', () => {
      console.log('Disconnected');
    });

    socket.on('update_thread', thread_update => {
      var new_thread_states = JSON.parse(JSON.stringify(this.state.thread_states));
      var new_thread_locs = JSON.parse(JSON.stringify(this.state.thread_locs));
      // first remove its old location in thread_locs
      for (var loc in new_thread_locs) {
        // search for the previous location of the thread ID in thread_locs
        if (new_thread_locs.hasOwnProperty(loc) && new_thread_locs[loc] === thread_update[0]) {
            delete new_thread_locs[loc];
        }
    }
      new_thread_states[thread_update[0]] = [thread_update[1], thread_update[2]];
      new_thread_locs[thread_update[1]] = thread_update[0];
      this.setState({ thread_states: new_thread_states, thread_locs: new_thread_locs});
    });

    socket.on('kill_thread', thread_id => {
      var new_thread_states = JSON.parse(JSON.stringify(this.state.thread_states));
      var new_thread_locs = JSON.parse(JSON.stringify(this.state.thread_locs));
      if (thread_id in new_thread_locs) {
        delete new_thread_locs[new_thread_states[thread_id][0]];
        delete new_thread_states[thread_id];
      }
      this.setState({ thread_states: new_thread_states, thread_locs: new_thread_locs});
    });

    socket.on('core_connection', core => {
      var colified_core = core.map(byte => {
        return "#" + (255 - byte).toString(16).repeat(3);
      });
      this.setState({ core_state: colified_core });
    });

    socket.on('core_state', updates => {
      var core = [...this.state.core_state];
      updates.forEach(update => {
        core[update[0]] = "#" + (255 - update[1]).toString(16).repeat(3);
      });

      this.setState({ core_state: core });
    });
    

    this.setState({ socket });
  }

  render() {
    const { classes } = this.props;
    const { core_state, thread_locs, thread_states } = this.state;

    return (
      <div className={classes.grid}>
          {core_state.map((data, idx) =>
            {
              if (!(idx in thread_locs)) {
                return <div key={idx} className="box" style={{backgroundColor: data}}>
                </div>
              }
              else {
                return <div key={idx} className="box" style={{backgroundColor: thread_states[thread_locs[idx]][1]}}>
                </div>
              }
            } 
          )}
        </div>
    );
  }
}


export default withStyles(styles)(Core);