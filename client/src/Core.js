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
      width: '12px',
      'height': '12px',
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

  componentDidMount() {
    const { token } = this.props;

    const socket = io(':5000', {
      query: `token=${token}`,
    });

    socket.on('connect', () => {
      console.log("Connected!");
    });

    socket.on('disconnect', () => {
      console.log('Disconnected');
    });

    socket.on('update_thread', thread_updates => {
      const new_thread_states = thread_updates.reduce((prev, curr) => {
        const [id, pc, color] = curr

        prev[id] = [pc, color]

        return prev
      }, {})
      const new_thread_locs = thread_updates.reduce((prev, curr) => {
        const [id, pc] = curr

        prev[pc] = id

        return prev
      }, {})

      this.setState({ thread_states: new_thread_states, thread_locs: new_thread_locs })
    });

    socket.on('kill_thread', thread_ids => {
      thread_ids.forEach(thread_id => {
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
      })
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
        {core_state.map((data, idx) => {
          if (!(idx in thread_locs)) {
            return <MemoryCell key={idx} bgColor={data} />
          }
          else {
            const bgColor = thread_states[thread_locs[idx]][1]

            return <MemoryCell key={idx} bgColor={bgColor} />
          }
        }
        )}
      </div>
    );
  }
}

const MemoryCell = React.memo(function MemoryCell({
  bgColor,
}) {
  return (
    <div className="box" style={{ backgroundColor: bgColor }} />
  )
})


export default withStyles(styles)(Core);