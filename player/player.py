import json
import asyncio

import websockets
import websockets.exceptions
import numpy as np

from decoder import Decoder
from misc_helpers import shiftSamples


class Player:
    """Fake player of game.

    Pretends to have sensors which we repeatdly measure, based on the state of the game,
    like where the cursor is and where the goal is.

    Hosts a WebSocket server with which to receive messages from other components.
    """

    def __init__(
        self,
        wsHost,
        wsPort,
        numChannels=192,
        restingMeansRange=(-10, 10),
        restingStdDevRange=(0.1, 0.3),
        measurementInterval_sec=0.01,
    ):
        """
        :param str wsHost: ip address where this player's ws server can be reached
        :param int wsPort: port where this player's ws server can be reached
        :param int numChannels: e.g. number of electrodes we are measuring
        :param (float, float) restingMeansRange: interval from which to choose random
            means for the channels
        :param (float, float) restingStdDevRange: interval from which to choose random
            standard deviations for the channels
        :param float measurementInterval_sec: seconds between each sampling of the
            player's state
        """
        # How many things can we measure (e.g. how many sensors, or electrodes, etc.).
        self.numChannels = numChannels
        # Generator of randomness.
        self.randGenerator = np.random.default_rng()
        # Current readings of the sensors.
        self.measurements = None
        # Mean value of each channel when no input from game.
        self.restingMeans = shiftSamples(
            self.randGenerator.random(self.numChannels), restingMeansRange
        )
        # Standard deviation of each channel when no input from game.
        self.restingStdDevs = shiftSamples(
            self.randGenerator.random(self.numChannels), restingStdDevRange
        )
        # Seconds between each sampling of the player's state.
        self.measurementInterval_sec = measurementInterval_sec

        # Decoder trained to look at the measurements and decide what to do in the game.
        self.decoder = Decoder()

        # Parameters of WebSocket server used to receive messages from other components.
        self.wsHost = wsHost
        self.wsPort = wsPort
        # WebSocket with which to send messages to the game.
        self.websocket = None
        # Latest state we've heard from the game.
        self.gameState = None

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
        while True:
            self.updateMeasurements(self.gameState)
            await asyncio.sleep(self.measurementInterval_sec)

    def updateMeasurements(self, gameState):
        """Based on the state of the game, generate new values for this player's current
        measurements.

        :param dict gameState: see API documentation in README for structure of these
            game state updates sent via WebSocket
        """
        newMeasurements = self.randGenerator.normal(
            self.restingMeans, self.restingStdDevs
        )

        ## TODO: when gameState["cursor"] position is to the left of gameState["target"]
        ##      then resample for certain indices with a different special mean. Do this
        ##      for each of left, right, up, down.

        self.measurements = newMeasurements

    async def decoderLoop(self):
        """Repeatedly decode the current measurements to generate commands to send to
        the game, since the measurements should hold the info (in a non-obvious way,
        hence the need for the decoder) of what's happening in the game.
        """
        gameCommandInterval = 0.01
        while True:
            if self.measurements is not None and self.websocket is not None:
                gameCommand = self.decoder.decode(self.measurements)
                msgDict = {"TYPE": "GAME_COMMAND", "PAYLOAD": gameCommand}
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


async def main():
    HOST = "localhost"
    PORT = 1530

    print("\nStarting player...\n")
    await Player(HOST, PORT, measurementInterval_sec=1).start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nReceived interrupt. Ending process...\n")
