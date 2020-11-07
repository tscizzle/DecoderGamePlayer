import _ from "lodash";
import Phaser from "phaser";

import { connect, send } from "ws-client";
import { GAME_WIDTH, GAME_HEIGHT } from "game-constants";

class MainScene extends Phaser.Scene {
  PLAYER_WS_HOST = "localhost";
  PLAYER_WS_PORT = 1530;

  constructor() {
    super("MainScene");

    connect({ host: this.PLAYER_WS_HOST, port: this.PLAYER_WS_PORT });
  }

  /* MAIN PHASER METHODS */

  create() {
    /* Constants */
    this.SCREEN_CENTER = { x: GAME_WIDTH / 2, y: GAME_HEIGHT / 2 };
    this.MOVE_GAIN = 400;

    /* Objects */
    // Create a player cursor out of some shapes.
    this.playerCursor = this.add.container(
      this.SCREEN_CENTER.x,
      this.SCREEN_CENTER.y
    );
    const star = this.add.star(0, 0, 5, 20, 40, 0xfafafa);
    const circle = this.add.circle(0, 0, 40);
    circle.setStrokeStyle(2, 0xfafafa);
    this.playerCursor.add([star, circle]);
    // Add a Physics Body to the player cursor so it can move.
    this.physics.add.existing(this.playerCursor);
    this.playerCursor.body.collideWorldBounds = true;

    /* Control */
    this.moveControls = this.input.keyboard.createCursorKeys();
  }

  update() {
    /* Player movement */
    // Set the direction vector based on user input.
    const direction = new Phaser.Math.Vector2();
    if (this.moveControls.left.isDown) {
      direction.x = -1;
    } else if (this.moveControls.right.isDown) {
      direction.x = 1;
    }
    if (this.moveControls.down.isDown) {
      direction.y = 1;
    } else if (this.moveControls.up.isDown) {
      direction.y = -1;
    }
    // Set the magnitude based on the configured speed.
    direction.normalize().scale(this.MOVE_GAIN);
    // Move the player.
    this.playerCursor.body.setVelocity(direction.x, direction.y);

    /* Send out a game state update message. */
    const gameState = {
      cursor: { x: this.playerCursor.body.x, y: this.playerCursor.body.y },
    };
    const gameStateMsg = {
      TYPE: "GAME_UPDATE",
      PAYLOAD: { gameState },
    };
    send(JSON.stringify(gameStateMsg));
  }
}

export default MainScene;
