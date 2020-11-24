import json
import asyncio
from datetime import datetime, timezone

import websockets
import websockets.exceptions
import numpy as np


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
        # Current readings of the sensors.
        self.measurements = np.zeros(numChannels)
        # Latest state we've heard from the game.
        self.gameState = None
        # Decoder trained to look at the measurements and decide what to do in the game.
        self.decoder = Decoder()
        # WebSocket with which to send messages to the game.
        self.websocket = None

    async def start(self):
        """Kick off the various loops this player performs."""
        # Task for repeatedly taking measurements.
        measurementCoro = asyncio.create_task(self.measurementLoop())
        # Task for repeatedly decoding the measurements and sending game commands.
        decoderCoro = asyncio.create_task(self.decoderLoop())
        # Task for listening for WebSocket connections and messages.
        wsServerCoro = websockets.serve(
            self.connectionHandler, self.wsHost, self.wsPort
        )
        await asyncio.gather(measurementCoro, decoderCoro, wsServerCoro)

    async def measurementLoop(self):
        """Repeatedly read the sensors and store the values we see. We pretend that the
        player is playing the game and thus the measurements we get depend on what is
        happening in the game.
        """
        measurementInterval = 0.01
        while True:
            self.updateMeasurements(self.gameState)
            await asyncio.sleep(measurementInterval)

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

    async def decoderLoop(self):
        """Repeatedly decode the current measurements to generate commands to send to
        the game, since the measurements should hold the info (in a non-obvious way,
        hence the need for the decoder) of what's happening in the game.
        """
        gameCommandInterval = 0.01
        while True:
            if self.websocket is not None:
                gameCommand = self.decoder.decode(self.measurements)
                msgDict = {
                    "TYPE": "GAME_COMMAND",
                    "PAYLOAD": gameCommand
                }
                msg = json.dumps(msgDict)
                try:
                    await self.websocket.send(msg)
                except websockets.exceptions.ConnectionClosed:
                    self.websocket = None
            await asyncio.sleep(gameCommandInterval)

    async def connectionHandler(self, websocket, path):
        """Called once per connection to this component's WebSocket server. Simply keep
        looping through all messages received on that connection and handle each one.

        Signature set by `websockets` library, specifically the `serve` method.

        :param websockets.WebSocketServerProtocol websocket:
        :param str path:
        """
        _ = path
        # Save this WebSocket on the class, for sending messages.
        self.websocket = websocket
        # Forever loop and receive incoming WebSocket messages.
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
        the game and thus output a game command.

        :param np.array measurements: same structure as Player.measurements

        :return dict gameCommand: see WebSocket API of the game for how to structure
            commands
        """
        ## TODO: make this actually figure out what `measurements` is saying about the
        ##      game (this is where we'll employ our learning techniques, like neural
        ##      nets)
        gameCommand = {
            "move": {"x": 1, "y": 2},
            "timestring": datetime.now(tz=timezone.utc).isoformat()
        }
        return gameCommand


async def main():
    HOST = "localhost"
    PORT = 1530

    print("\nStarting player...\n")
    await Player(HOST, PORT).start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nReceived interrupt. Ending process...\n")
