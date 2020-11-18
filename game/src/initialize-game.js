import Phaser from "phaser";

import { GAME_WIDTH, GAME_HEIGHT } from "game-constants";
import MainScene from "main-scene";

const initializeGame = ({ parent }) => {
  const gameConfig = {
    width: GAME_WIDTH,
    height: GAME_HEIGHT,
    scene: [MainScene],
    physics: {
      default: "arcade",
    },
    type: Phaser.AUTO,
    parent,
  };
  const game = new Phaser.Game(gameConfig);
  return game;
};

export default initializeGame;
