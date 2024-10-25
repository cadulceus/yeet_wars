import React, { Component } from 'react';
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom';
import Core from './Core';
import Events from './Events';
import { withStyles } from '@material-ui/core';
import io from 'socket.io-client';


const styles = theme => ({
  bigForm: {
    width: '100%',
    height: '100vh',
    display: 'flex',
    'flex-direction': 'column',
    'justify-content': 'center',
    'align-items': 'center',
    'font-size': '32px',
  },
});


class App extends Component {
  constructor(props) {
    super(props);
    this.state = { 
      socket: null
    };
  }
  componentDidMount() {
    const token = query.get('token');

    const socket = io(':5000', {
      query: `token=${token}`,
    });

    this.setState({ socket });
  }

  render() {
    const query = new URLSearchParams(window.location.search);
    const token = query.get('token');

    const { classes } = this.props;

    if (!token) return (
      <form className={classes.bigForm}>
        <label htmlFor="token">Token</label>
        <input type="text" name="token" />
      </form>
    );

    return(
      <Router>
        <div>
          <nav>
            <ul>
              <li>
                <a href="/">Core</a>
              </li>
              <li>
                <Link to="/events">Events</Link>
              </li>
            </ul>
          </nav>

          <Switch>
            <Route exact path="/">
              <Core token={token} socket={this.state.socket} />
            </Route>
            <Route exact path="/events">
              <Events token={token} socket={this.state.socket} />
            </Route>
          </Switch>
        </div>
      </Router>
    );
  }
}

export default withStyles(styles)(App);
