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
    this.CALIBRATION_TIME_LENGTH = 3 * 1000;
    this.CALIBRATION_RADIUS = 150;

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
    // Create a Calibrate button.
    this.isCalibrating = false;
    this.calibrateStartTime = -Infinity;
    this.calibrateButton = this.add.text(30, 30, "Calibrate");
    this.calibrateButton.setInteractive({ useHandCursor: true });
    this.calibrateButton.on(
      "pointerup",
      () => (this.calibrateStartTime = new Date())
    );

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
    // If calibrating, hard-code the movement instead of taking any input.
    const timeSinceCalibrationStarted = new Date() - this.calibrateStartTime;
    this.isCalibrating =
      timeSinceCalibrationStarted < this.CALIBRATION_TIME_LENGTH;
    if (this.isCalibrating) {
      // Set the target to be in the middle.
      this.target.setPosition(this.SCREEN_CENTER.x, this.SCREEN_CENTER.y);
      // Set the player to move around the target in a circle.
      const angle =
        (timeSinceCalibrationStarted / this.CALIBRATION_TIME_LENGTH) *
        2 *
        Math.PI;
      const cursorX =
        this.SCREEN_CENTER.x + Math.cos(angle) * this.CALIBRATION_RADIUS;
      const cursorY =
        this.SCREEN_CENTER.y + Math.sin(angle) * this.CALIBRATION_RADIUS;
      this.playerCursor.setPosition(cursorX, cursorY);
    } else {
      let direction = new Phaser.Math.Vector2(0, 0);
      // Set the direction based on received commands.
      if (!_.isEmpty(this.queuedCommands)) {
        const commandIds = _.keys(this.queuedCommands);
        const commands = _.map(
          commandIds,
          (commandId) => this.queuedCommands[commandId]
        );
        const latestCommand = _.maxBy(
          commands,
          ({ timestring }) => new Date(timestring)
        );
        direction.x = latestCommand.move.x;
        direction.y = -latestCommand.move.y;
        // Remove the commands we've processed.
        _.each(
          commandIds,
          (commandId) => delete this.queuedCommands[commandId]
        );
      }
      // Set the direction vector based on user input. (If there is any user
      // input, it overrides received commands.)
      const userInputDirection = new Phaser.Math.Vector2();
      if (this.moveControls.left.isDown) {
        userInputDirection.x = -1;
      } else if (this.moveControls.right.isDown) {
        userInputDirection.x = 1;
      }
      if (this.moveControls.down.isDown) {
        userInputDirection.y = 1;
      } else if (this.moveControls.up.isDown) {
        userInputDirection.y = -1;
      }
      if (userInputDirection.length() > 0) {
        direction = userInputDirection;
      }
      // Set the magnitude based on the configured speed.
      direction.normalize().scale(this.MOVE_GAIN);
      // Move the player.
      this.playerCursor.body.setVelocity(direction.x, direction.y);
    }

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
        y: GAME_HEIGHT - this.playerCursor.body.y,
        radius: this.PLAYER_SIZE,
      },
      target: {
        x: this.target.body.x,
        y: GAME_HEIGHT - this.target.body.y,
        radius: this.PLAYER_SIZE,
      },
      isCalibrating: this.isCalibrating,
    };
    const timestring = new Date().toISOString().replace("Z", "+00:00");
    const gameStateMsg = {
      TYPE: "GAME_UPDATE",
      PAYLOAD: { gameState, timestring },
    };
    send(JSON.stringify(gameStateMsg));
  };
}

export default MainScene;
