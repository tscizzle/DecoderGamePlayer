import React, { Component } from 'react';

import initializeGame from 'initialize-game';

import 'stylesheets/app.css';

class App extends Component {
  containerId = 'game-container';

  componentDidMount() {
    initializeGame({ parent: this.containerId });
  }

  render() {
    return (
      <div className="app">
        <div id={this.containerId} />
      </div>
    );
  }
}

export default App;
