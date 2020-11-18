import _ from "lodash";
import Phaser from "phaser";

import { connect, send } from "ws-client";
import { GAME_WIDTH, GAME_HEIGHT } from "game-constants";

class MainScene extends Phaser.Scene {
  PLAYER_WS_HOST = "localhost";
  PLAYER_WS_PORT = 1530;

  /* MAIN PHASER METHODS */

  create() {
    /* Constants */
    this.SCREEN_CENTER = { x: GAME_WIDTH / 2, y: GAME_HEIGHT / 2 };
    this.MOVE_GAIN = 400;
    this.PLAYER_SIZE = 20;
    this.TARGET_SIZE = 20;
    this.MIN_NEW_TARGET_DIST = _.min([GAME_WIDTH, GAME_HEIGHT]) / 3;

    /* Objects */
    // Create a player cursor out of some shapes.
    this.playerCursor = this.add.container(
      this.SCREEN_CENTER.x,
      this.SCREEN_CENTER.y
    );
    this.playerCursor.setSize(this.PLAYER_SIZE * 2, this.PLAYER_SIZE * 2);
    const star = this.add.star(
      0,
      0,
      5,
      this.PLAYER_SIZE / 2,
      this.PLAYER_SIZE,
      0xfafafa
    );
    const circle = this.add.circle(0, 0, this.PLAYER_SIZE);
    circle.setStrokeStyle(2, 0xfafafa);
    this.playerCursor.add([star, circle]);
    // Add a Physics Body to the player cursor so it can move.
    this.physics.add.existing(this.playerCursor);
    this.playerCursor.body.collideWorldBounds = true;
    this.playerCursor.body.setCircle(this.PLAYER_SIZE);
    // Create a target circle.
    const targetPosition = this.getNewTargetPosition();
    this.target = this.add.circle(
      targetPosition.x,
      targetPosition.y,
      this.TARGET_SIZE,
      0xfafafa
    );
    // Add a Physics Body to the target so it can collide with the player
    // cursor.
    this.physics.add.existing(this.target);
    this.target.body.setCircle(this.TARGET_SIZE);

    /* Controls */
    this.moveControls = this.input.keyboard.createCursorKeys();
    this.queuedCommands = {};

    /* Connect to Player WebSocket server */
    connect({
      host: this.PLAYER_WS_HOST,
      port: this.PLAYER_WS_PORT,
      handleMessage: this.handleWsMsg,
    });
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
    /* TODO: if there is anything in this.queuedCommands, grab the keys, take
    the command with the latest timestring, apply it to get the movement
    direction, then delete the grabbed keys from this.queuedCommands (this
    keys technique avoids concurrency issues like a normal array would have).
    */
    console.log(_.size(this.queuedCommands));
    // Set the magnitude based on the configured speed.
    direction.normalize().scale(this.MOVE_GAIN);
    // Move the player.
    this.playerCursor.body.setVelocity(direction.x, direction.y);

    /* Reaching the target */
    this.physics.overlap(this.playerCursor, this.target, () => {
      const newPosition = this.getNewTargetPosition();
      this.target.setPosition(newPosition.x, newPosition.y);
    });

    /* Send out a game state update message. */
    this.sendGameStateUpdateMsg();
  }

  // HELPERS

  getNewTargetPosition = () => {
    /* Return a random new target position ({ x, y }) but make sure it is not
      trivially close to the cursor already.
    
    :return Phaser.Math.Vector2 newPosition:
    */

    // Our strategy is to randomly suggest a position but reject it if it's too
    // close and try again. Cap how many times we try, so we don't accidentally
    // infinitely loop.
    const maxTries = 100;
    let numTriesSoFar = 0;
    while (numTriesSoFar < maxTries) {
      const newX = Math.random() * GAME_WIDTH;
      const newY = Math.random() * GAME_HEIGHT;
      const newPosition = new Phaser.Math.Vector2(newX, newY);
      const isFarEnough =
        this.playerCursor.body.position.distance(newPosition) >=
        this.MIN_NEW_TARGET_DIST;
      if (isFarEnough) {
        return newPosition;
      }
      numTriesSoFar += 1;
    }
    // If we reach here, something is wrong.
    throw "Unable to find new target position.";
  };

  handleWsMsg = (msgObj) => {
    /* Handle an incoming WebSocket message. */
    const { TYPE, PAYLOAD } = msgObj;

    if (TYPE === "GAME_COMMAND") {
      const commandId = Math.random();
      this.queuedCommands[commandId] = PAYLOAD;
    } else {
      console.info(`Unrecognized TYPE: ${TYPE}`);
    }
  };

  sendGameStateUpdateMsg = () => {
    /* Construct a summary object of the game state (player position, target
      position, etc.) and send it to the Player component via WebSocket.
    */
    const gameState = {
      playerCursor: {
        x: this.playerCursor.body.x,
        y: this.playerCursor.body.y,
        radius: this.PLAYER_SIZE,
      },
      target: {
        x: this.target.body.x,
        y: this.target.body.y,
        radius: this.PLAYER_SIZE,
      },
    };
    const gameStateMsg = {
      TYPE: "GAME_UPDATE",
      PAYLOAD: { gameState },
    };
    send(JSON.stringify(gameStateMsg));
  };
}

export default MainScene;
