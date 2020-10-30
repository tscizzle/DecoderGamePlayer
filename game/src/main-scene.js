import _ from 'lodash';
import Phaser from 'phaser';

import { GAME_WIDTH, GAME_HEIGHT } from 'game-constants';

class MainScene extends Phaser.Scene {
  constructor() {
    super('MainScene');
  }

  /* MAIN PHASER METHODS */

  preload() {
    console.log('Preloading...');
    console.log('Preloaded.');
  }

  create() {
    console.log('Creating...');
    console.log('Created.');
  }

  update() {
    // TODO: make the game
  }
}

export default MainScene;
