import React, { Component } from 'react';
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
      width: '12px',
      'height': '12px',
    },
  },
});

class Core extends Component {
  constructor(props) {
    super(props);

    this.state = {
      core_state: [],
      thread_states: {},
      thread_locs: {}
    }
  }

  componentDidMount(){
    this.props.socket.on('connect', () => {
      console.log("Connected!");
    });

    this.props.socket.on('disconnect', () => {
      console.log('Disconnected');
    });

    this.props.socket.on('update_thread', thread_update => {
      const [id, pc, color] = thread_update;

      var new_thread_states = JSON.parse(JSON.stringify(this.state.thread_states));
      var new_thread_locs = JSON.parse(JSON.stringify(this.state.thread_locs));
      // first remove its old location in thread_locs
      for (var loc in new_thread_locs) {
        // search for the previous location of the thread ID in thread_locs
        if (new_thread_locs.hasOwnProperty(loc) && new_thread_locs[loc] === id) {
            delete new_thread_locs[loc];
        }
      }
      new_thread_states[id] = [pc, color];
      new_thread_locs[pc] = id;
      this.setState({ thread_states: new_thread_states, thread_locs: new_thread_locs});
    });

    this.props.socket.on('kill_thread', thread_id => {
      const { thread_states, thread_locs } = this.state;

      this.setState({
        thread_states: Object.keys(thread_states).filter(key => key !== thread_id).reduce((states, tid) => {
          states[tid] = thread_states[tid];
          return states;
        }, {}),
        thread_locs: Object.keys(thread_locs).filter(key => thread_locs[key] !== thread_id
          ).reduce((locs, loc) => {
            locs[loc] = thread_locs[loc];
            return locs;
          }, {}),
      });
    });

    this.props.socket.on('core_connection', core => {
      var colified_core = core.map(byte => {
        return "#" + (255 - byte).toString(16).repeat(3);
      });
      this.setState({ core_state: colified_core });
    });

    this.props.socket.on('core_state', updates => {
      var core = [...this.state.core_state];
      console.log(updates)
      updates.forEach(update => {
        core[update[0]] = "#" + (255 - update[1]).toString(16).repeat(3);
      });

      this.setState({ core_state: core });
    });
    
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