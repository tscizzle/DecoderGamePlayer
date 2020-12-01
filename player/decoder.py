from datetime import datetime, timezone

import numpy as np


class Decoder:
    """Decoder of the player's measurements into game commands."""

    def __init__(self, inputShape, outputShape):
        """
        :param tuple[float] inputShape: shape of each sample (e.g. (192,) if each sample
            is a 1-D array of length 192)
        :param tuple[int] outputShape: shape of each answer (e.g. (1,) if each answer is
            a 1-D array of length 1)
        """
        self.inputShape = inputShape
        self.outputShape = outputShape

        # With the following shape, self.trainingInputs is an array of 0 elements, each
        # of shape inputShape. E.g. np.empty((0, 192)) can have a 1-D array of length
        # 192 appended to it, so it becomes shape (1, 192), then another makes it
        # (2, 192), etc.
        self.trainingInputs = np.empty((0, *self.inputShape))
        # Same thing with trainingAnswers.
        self.trainingAnswers = np.empty((0, *self.outputShape))

        ## TODO: create an SVM model using scipy's scikit learn or whatever
        self.svmModel = None

    def addToTrainingData(self, inp, ans):
        """Given an input, and the correct output, add to the stored training data.

        :param np.array inp: array of shape
        :param ans:
        """
        self.trainingInputs = np.vstack((self.trainingInputs, inp))
        self.trainingAnswers = np.vstack((self.trainingAnswers, ans))

    def decode(self, measurements):
        """Given measurements of the player, predict what that player is trying to do in
        the game and thus output a game command.

        :param np.array measurements: same structure as Player.measurements

        :return dict gameCommand: see WebSocket API of the game for how to structure
            commands
        """
        ## TODO: use self.svmModel to figure out what `measurements` is saying about the
        ##      game
        if self.svmModel is None:
            return
        gameCommand = {
            "move": {"x": 1, "y": 2},
            "timestring": datetime.now(tz=timezone.utc).isoformat(),
        }
        return gameCommand
