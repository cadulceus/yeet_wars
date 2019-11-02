import React, { Component } from 'react';
import { BrowserRouter as Router, Switch, Route, Link } from 'react-router-dom';
import Core from './Core';
import Events from './Events';

// const styles = theme => ({
//   root: {
//     display: 'flex',
//     'flex-direction': 'column',
//     'align-items': 'baseline',
//     'justify-content': 'center',
//   },
//   title: {
//     width: '100%',
//     display: 'flex',
//     'justify-content': 'center',
//     'font-size': "32px",
    
//     'padding': '1em',
//   },
//   grid: {
//     display: 'flex',
//     'flex-direction': 'row',
//     'justify-content': 'center',
//     'align-items': 'baseline',
//     'width': '100%',
//     'box-sizing': 'border-box',
//     'flex-wrap': 'wrap',
//     padding: '1em',

//     '& > div': {
//       width: '20px',
//       'height': '20px',
//     },
//   },
// });


class App extends Component {
  render() {

    return(
      <Router>
        <div>
          <nav>
            <ul>
              <li>
                <Link to="/">Core</Link>
              </li>
              <li>
                <Link to="/events">Events</Link>
              </li>
            </ul>
          </nav>

          <Switch>
            <Route exact path="/">
              <Core />
            </Route>
            <Route exact path="/events">
              <Events />
            </Route>
          </Switch>
        </div>
      </Router>
    );
  }
}

export default App;
