import json
import asyncio
from datetime import datetime, timezone
import traceback
import time

import websockets
import websockets.exceptions
import numpy as np
from matplotlib import pyplot as plt

from decoder import Decoder
from misc_helpers import shiftSamples


HOST = "localhost"
PORT = 1530

glob = {}


class Player:
    """Fake player of game.

    Pretends to have sensors which we repeatdly measure, based on the state of the game,
    like where the cursor is and where the goal is.

    Hosts a WebSocket server with which to receive messages from other components.
    """

    def __init__(self, wsHost, wsPort):
        """
        :param str wsHost: ip address where this player's ws server can be reached
        :param int wsPort: port where this player's ws server can be reached
        """
        # How many things can we measure (e.g. how many sensors, or electrodes, etc.).
        self.numChannels = 192
        # Generator of randomness.
        self.randGenerator = np.random.default_rng()
        # Current readings of the sensors.
        self.currentMeasurements = None
        # Keep some recent history of measurements.
        self.historicalMeasurements = np.empty((0, self.numChannels))
        # How many steps of historical measurements to remember.
        self.measurementHistoryLength = 30
        # Mean value of each channel when no input from game.
        self.restingMeansRange = (-10, 10)
        self.restingMeans = shiftSamples(
            self.randGenerator.random(self.numChannels), self.restingMeansRange
        )
        # Standard deviation of each channel when no input from game.
        self.restingStdDevsRange = (0.1, 0.3)
        self.restingStdDevs = shiftSamples(
            self.randGenerator.random(self.numChannels), self.restingStdDevsRange
        )
        # For each of the 4 cursor directions, have a channel associated with it.
        random4Channels = self.randGenerator.choice(
            self.numChannels, size=4, replace=False
        )
        self.directionTunedIndices = {
            "up": random4Channels[0],
            "right": random4Channels[1],
            "down": random4Channels[2],
            "left": random4Channels[3],
        }
        # How much a direction-tuned channel's mean changes.
        self.directionTunedMeanShift = 4

        # Decoder trained to look at the measurements and decide what to do in the game.
        self.decoder = Decoder(inputShape=(self.numChannels,))

        # Parameters of WebSocket server used to receive messages from other components.
        self.wsHost = wsHost
        self.wsPort = wsPort
        # WebSocket with which to send messages to the game.
        self.gameWebSocket = None
        # Latest state we've heard from the game.
        self.gameState = None

        # Real-time visualization of measurements.
        numSpecialChannels = 4  # currently just 4 direction-tuned channels
        self.lines = {}
        self.fig, self.axs = plt.subplots(numSpecialChannels)
        # self.initializeVisualization()

        # Allow pausing of all coroutines to let a human inspect things.
        self.isPaused = False

    async def start(self):
        """Kick off the various loops this player performs."""
        coroutines = [
            # Task for taking measurements.
            asyncio.create_task(self.measurementLoop()),
            # Task for training the model.
            asyncio.create_task(self.trainingLoop()),
            # Task for decoding the measurements and sending game commands.
            asyncio.create_task(self.decodingLoop()),
            # Task for listening for WebSocket connections and messages.
            websockets.serve(self.connectionHandler, self.wsHost, self.wsPort),
            # Task for real-time data visualization.
            # asyncio.create_task(self.visualizationLoop()),
        ]

        # Run all the tasks.
        await asyncio.gather(*coroutines)

    async def loopWhilePaused(self):
        """Block until the program is unpaused.

        Call this at the top of every coroutine's loop to allow pausing of everything.
        """
        pauseInterval = 0.01
        while self.isPaused:
            await asyncio.sleep(pauseInterval)

    def pause(self):
        """Pause all the coroutine loops."""
        print("Pausing...")
        self.isPaused = True

    def unpause(self):
        """Unpause all the coroutine loops."""
        print("Unpausing...")
        self.isPaused = False

    async def measurementLoop(self):
        """Repeatedly read the sensors and store the values we see. We pretend that the
        player is playing the game and thus the measurements we get depend on what is
        happening in the game.
        """
        measurementInterval = 0.01
        while True:
            await self.loopWhilePaused()
            self.updateMeasurements(self.gameState)
            await asyncio.sleep(measurementInterval)

    def updateMeasurements(self, gameState):
        """Based on the state of the game, generate new values for this player's current
        measurements.

        :param dict gameState: see API documentation in README for structure of these
            game state updates sent via WebSocket
        """
        if gameState is None:
            return

        # "Measure" each channel, by getting a random value based on the "resting" mean
        # and standard deviation for each channel.
        newMeasurements = self.randGenerator.normal(
            self.restingMeans, self.restingStdDevs
        )

        # Depending on what direction the target is from the player cursor, have some
        # channels (the direction-tuned ones) use a different mean.
        playerX = gameState["playerCursor"]["x"]
        playerY = gameState["playerCursor"]["y"]
        targetX = gameState["target"]["x"]
        targetY = gameState["target"]["y"]
        channelsWithShiftedMean = []
        if targetY > playerY:
            channelIdx = self.directionTunedIndices["up"]
            channelsWithShiftedMean.append(channelIdx)
        elif targetY < playerY:
            channelIdx = self.directionTunedIndices["down"]
            channelsWithShiftedMean.append(channelIdx)
        if targetX > playerX:
            channelIdx = self.directionTunedIndices["right"]
            channelsWithShiftedMean.append(channelIdx)
        elif targetX < playerX:
            channelIdx = self.directionTunedIndices["left"]
            channelsWithShiftedMean.append(channelIdx)
        # Resample for the relevant direction-tuned channels, with their new means.
        for channelIdx in channelsWithShiftedMean:
            newMean = self.restingMeans[channelIdx] + self.directionTunedMeanShift
            stdDev = self.restingStdDevs[channelIdx]
            newMeasurements[channelIdx] = self.randGenerator.normal(newMean, stdDev)

        # Update currentMeasurements.
        self.currentMeasurements = newMeasurements
        # Update historicalMeasurements.
        self.historicalMeasurements = np.vstack(
            (self.historicalMeasurements, newMeasurements)
        )
        if len(self.historicalMeasurements) > self.measurementHistoryLength:
            self.historicalMeasurements = self.historicalMeasurements[1:]

        # If calibrating, update the decoder's training data.
        if self.gameState["isCalibrating"]:
            moreVertical = abs(targetY - playerY) > abs(targetX - playerX)
            if moreVertical:
                answer = "up" if targetY > playerY else "down"
            else:
                answer = "right" if targetX > playerX else "left"
            self.decoder.addToTrainingData(self.currentMeasurements, answer)

    async def trainingLoop(self):
        """Periodically train the model on the training data received so far. Don't
        re-train if no new data has arrived.
        """
        trainingInterval = 1
        while True:
            await self.loopWhilePaused()
            if self.decoder.isNewDataSinceLastTrained:
                self.decoder.train()
            await asyncio.sleep(trainingInterval)

    async def decodingLoop(self):
        """Repeatedly decode the current measurements to generate commands to send to
        the game, since the measurements should hold the info (in a non-obvious way,
        hence the need for the decoder) of what's happening in the game.
        """
        gameCommandInterval = 0.01
        while True:
            await self.loopWhilePaused()
            if (
                self.currentMeasurements is not None
                and self.gameWebSocket is not None
                and self.decoder.hasBeenTrainedAtAll
            ):
                timestring = datetime.now(tz=timezone.utc).isoformat()
                gameCommand = self.decoder.decode(self.currentMeasurements)
                if gameCommand is not None:
                    gameCommand["timestring"] = timestring
                    msgDict = {"TYPE": "GAME_COMMAND", "PAYLOAD": gameCommand}
                    msg = json.dumps(msgDict)
                    try:
                        await self.gameWebSocket.send(msg)
                    except websockets.exceptions.ConnectionClosed:
                        print(
                            "In decoder loop, found Game WebSocket connection closed."
                        )
                        self.gameWebSocket = None
            await asyncio.sleep(gameCommandInterval)

    async def connectionHandler(self, websocket, path):
        """Called once per connection to this component's WebSocket server. Simply keep
        looping through all messages received on that connection and handle each one.

        Signature set by `websockets` library, specifically the `serve` method.

        :param websockets.WebSocketServerProtocol websocket:
        :param str path:
        """
        _ = path
        print("WebSocket connection open.")
        # Forever loop and receive incoming WebSocket messages.
        async for message in websocket:
            messageDict = json.loads(message)
            await self.messageHandler(messageDict, websocket)
        print("WebSocket connection closed.")

    async def messageHandler(self, messageDict, websocket):
        """Called once per incoming WebSocket message.

        :param dict messageDict: Keys "TYPE" and "PAYLOAD". More details on the API
            found in `player/README.md`.
        :param websockets.WebSocketServerProtocol websocket:
        """
        if messageDict["TYPE"] == "PYTHON_CODE":
            pythonCode = messageDict["PAYLOAD"]["pythonCode"]
            if not self.isPaused:
                self.pause()
                time.sleep(0.5)  # Give coroutines a chance to pause.
            result = None
            print(f"Evaluating `{pythonCode}`...")
            try:
                result = repr(eval(pythonCode))
                print("Completed.")
            except SyntaxError:
                print(f"Got SyntaxError, so trying `exec('{pythonCode}')`")
                try:
                    exec(pythonCode)
                    print("Completed.")
                except:
                    result = traceback.format_exc()
                    print("Errored.")
            except:
                result = traceback.format_exc()
                print("Errored.")
            msgDict = {"TYPE": "RESULT_OF_EVAL", "PAYLOAD": {"result": result}}
            msg = json.dumps(msgDict)
            await websocket.send(msg)

        # If paused, don't handle any messages, except the PYTHON_CODE message, so that
        # it is still possible to unpause things.
        if self.isPaused:
            return

        if messageDict["TYPE"] == "GAME_UPDATE":
            gameState = messageDict["PAYLOAD"]["gameState"]
            self.gameState = gameState
            self.gameWebSocket = websocket

    def initializeVisualization(self):
        """Create the figures used for real-time visualizations."""
        yMin = self.restingMeansRange[0] - (self.restingStdDevsRange[1] * 3)
        yMax = self.restingMeansRange[1] + (self.restingStdDevsRange[1] * 3)
        self.fig.suptitle("Historical Measurements")
        idx = 0
        for direction, channelIdx in self.directionTunedIndices.items():
            self.axs[idx].set_title(f"Channel {channelIdx} (tuned to '{direction}')")
            self.axs[idx].set_xlim((0, self.measurementHistoryLength))
            self.axs[idx].set_ylim((yMin, yMax))
            (line,) = self.axs[idx].plot([])
            self.lines[direction] = line
            idx += 1
        plt.tight_layout()  # auto-adjust margins between subplots
        plt.ion()  # allow updating data in real-time
        plt.show()

    async def visualizationLoop(self):
        """Display and update charts to visualize various data in real time."""
        visualizationInterval = 1
        while True:
            await self.loopWhilePaused()
            for direction, channelIdx in self.directionTunedIndices.items():
                line = self.lines[direction]
                # Values on the same channel over time.
                values = self.historicalMeasurements[:, channelIdx]
                # Send the update with the most recent data
                line.set_xdata(range(len(self.historicalMeasurements)))
                line.set_ydata(values)
            plt.pause(0.01)
            await asyncio.sleep(visualizationInterval)


def main():
    player = Player(HOST, PORT)

    try:
        print("Starting player...")
        asyncio.run(player.start())
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt...")


if __name__ == "__main__":
    main()
