import React, { Component } from "react";

import initializeGame from "initialize-game";

import "stylesheets/app.css";

class App extends Component {
  CONTAINER_ID = "game-container";

  componentDidMount() {
    initializeGame({ parent: this.CONTAINER_ID });
  }

  render() {
    return (
      <div className="app">
        <div id={this.CONTAINER_ID} />
      </div>
    );
  }
}

export default App;
