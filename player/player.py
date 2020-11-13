import json
import asyncio
from threading import Thread
import time

import websockets
import numpy as np


## TODO: do we need this, or can we see errors inside messageHandler?
# import logging
# logger = logging.getLogger('websockets.server')
# logger.setLevel(logging.ERROR)
# logger.addHandler(logging.StreamHandler())


class Player:
    """Fake player of game.

    Pretends to have sensors which we repeatdly measure, based on the state of the game,
    like where the cursor is and where the goal is.

    Hosts a WebSocket server with which to receive messages from other components.
    """

    def __init__(self, wsHost, wsPort, numChannels=192):
        """
        :param str wsHost:
        :param int wsPort:
        :param int numChannels:
        """
        # Parameters of WebSocket server used to receive messages from other components.
        self.wsHost = wsHost
        self.wsPort = wsPort
        # How many things can we measure (e.g. how many sensors, or electrodes, etc.).
        self.numChannels = numChannels
        # Current readings of the many sensors.
        self.measurements = np.zeros(numChannels)
        # How often do we read the sensors and update our measurements.
        self.measurementInterval = 0.01
        self.measurementInterval = 1
        # Latest state we've heard from the game.
        self.gameState = None

    def start(self):
        """Kick off the various loops this player performs."""
        # Start repeatedly taking measurements.
        Thread(target=self.measurementLoop, daemon=True).start()
        # Start listening for WebSocket connections and messages.
        self.startWebSocketServer(self.wsHost, self.wsPort)

    def measurementLoop(self):
        """Repeatedly read the sensors and store the values we see. We pretend that the
        player is playing the game and thus the measurements we get depend on what is
        happening in the game.
        """
        while True:
            self.updateMeasurements(self.gameState)
            time.sleep(self.measurementInterval)

    def updateMeasurements(self, gameState):
        """Based on the state of the game, generate new values for this player's current
        measurements.
        """
        if gameState is None:
            return
        ## TODO: make this something like each index having some mean value, and its
        ##      value is taken from a normal distribution around that val, and when
        ##      gameState["cursor"] position is to the left of gameState["goal"] then
        ##      certain indices have a new mean of the distribution from which their
        ##      value is taken.
        self.measurements = np.random.rand(self.numChannels)

    def startWebSocketServer(self, host, port):
        """Start the WebSocket server which connects with the game to receive
        updates.

        :param str host:
        :param int port:
        """
        startServer = websockets.serve(self.connectionHandler, host, port)

        asyncio.get_event_loop().run_until_complete(startServer)
        asyncio.get_event_loop().run_forever()

    async def connectionHandler(self, websocket, path):
        """Called once per connection to this component's WebSocket server. Simply keep
        looping through all messages received on that connection and handle each one.

        Signature set by `websockets` library, specifically the `serve` method.

        :param websockets.WebSocketServerProtocol websocket:
        :param str path:
        """
        _ = path
        async for message in websocket:
            messageDict = json.loads(message)
            self.messageHandler(messageDict)

    def messageHandler(self, messageDict):
        """Called once per incoming WebSocket message.

        :param dict messageDict: Keys "TYPE" and "PAYLOAD". More details on the API
            found in `player/README.md`.
        """
        if messageDict["TYPE"] == "GAME_UPDATE":
            gameState = messageDict["PAYLOAD"]["gameState"]
            self.gameState = gameState


class Decoder:
    """Decoder of the player's measurements into game commands."""

    def __init__(self):
        pass

    def decode(self, measurements):
        """Given measurements of the player, predict what that player is trying to do in
        the game and thus output game commands.

        :param np.array measurements: same structure as Player.measurements

        :return gameCommands: see WebSocket API of the game for how to structure
            commands
        """
        pass


def main():
    HOST = "localhost"
    PORT = 1530

    Player(HOST, PORT).start()


if __name__ == "__main__":
    main()
