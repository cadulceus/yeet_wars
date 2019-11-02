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
    };
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