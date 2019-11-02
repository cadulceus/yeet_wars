import React, { Component } from 'react';
import { withStyles } from '@material-ui/core';
import io from 'socket.io-client';

const styles = theme => ({

});

class Events extends Component {
  constructor(props) {
    super(props);


    this.state = {
      socket: io(':5000'),
      event_feed: []
    };
  }

  componentDidMount(){
    const { socket } = this.state;

    socket.on('connect', () => {
      console.log("Connected!");
    });
    
    socket.on('events', new_events => {
      var current_events = JSON.parse(JSON.stringify(this.state.event_feed));
      current_events.unshift(new_events);
      this.setState({ event_feed: current_events });
    });

    socket.on('disconnect', () => {
      // TODO: add a boundary to check for disconnect and render a "disconnected" error
    });
  }

  render() {
    const { classes } = this.props;

    return (
      <div className={classes.root}>
        <h1>Events</h1>
      </div>
    );
  }
}

export default withStyles(styles)(Events);