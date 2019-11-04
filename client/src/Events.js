import React, { Component } from 'react';
import { withStyles } from '@material-ui/core';
import io from 'socket.io-client';

const styles = theme => ({
  events_grid: {
    display: 'flex',
    'flex-direction': 'column',
    'justify-content': 'flex-start',
    'align-items': 'baseline',
    'min-width': '100%',
    'box-sizing': 'border-box',
    'flex-wrap': 'wrap',
    'white-space': 'pre-wrap',
    padding: '1em'
  },
    scores_grid: {
    display: 'flex',
    'flex-direction': 'column-reverse',
    'justify-content': 'flex-start',
    'align-items': 'baseline',
    'box-sizing': 'border-box',
    'flex-wrap': 'wrap',
    'white-space': 'pre-wrap',
    padding: '1em'
  },
});

class Events extends Component {
  constructor(props) {
    super(props);

    this.state = {
      socket: null,
      events: [],
      scores: []
    };
  }

  componentDidMount(){
    const { token } = this.props;

    const socket = io(':5000', {
      query: `token=${token}`,
    });

    socket.on('connect', () => {
      console.log("Connected to events!");
    });

    socket.on('player_scores', new_scores => {
      this.setState({ scores: new_scores });
    });
    
    socket.on('events', new_events => {
      var current_events = JSON.parse(JSON.stringify(this.state.events));
      current_events.unshift(new_events);
      if (current_events.length > 20) {
        current_events = current_events.slice(0, 20);
      }
      this.setState({ events: current_events });
    });

    socket.on('disconnect', () => {
      // TODO: add a boundary to check for disconnect and render a "disconnected" error
      console.log('disconnected');
    });

    this.setState({ socket });
  }

  render() {
    const { classes } = this.props;
    const { events } = this.state;
    const { scores } = this.state;

    return (
      <div>
        <div className={classes.scores_grid}>
          {scores.map((score, idx) =>
            <div key={idx} className="scores_box" style={{backgroundColor: score[1]}}> {score[0]}
            </div>  
          )}
        </div>
        <div className={classes.events_grid}>
          {events.map((event, idx) =>
            <div key={idx} className="event_box"> {event}
            </div>  
          )}
        </div>
      </div>
    );
  }
}

export default withStyles(styles)(Events);