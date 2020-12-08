import numpy as np
from sklearn import svm


class Decoder:
    """Decoder of the player's measurements into game commands."""

    def __init__(self, inputShape):
        """
        :param tuple[float] inputShape: shape of each sample (e.g. (192,) if each sample
            is a 1-D array of length 192)
        """
        self.inputShape = inputShape

        # With the following shape, self.trainingInputs is an array of 0 elements, each
        # of shape inputShape. E.g. np.empty((0, 192)) can have a 1-D array of length
        # 192 appended to it, so it becomes shape (1, 192), then another makes it
        # (2, 192), etc.
        self.trainingInputs = np.empty((0, *self.inputShape))
        # 1-D array of correct classifications of the training inputs ("up", "right",
        # "down", or "left").
        self.trainingAnswers = np.array([])

        # Object that handles the training and predicting using an SVM.
        self.svmModel = svm.LinearSVC()
        # Whether there is any new data since our model was last trained.
        self.isNewDataSinceLastTrained = False
        # Whether the model has been trained even once.
        self.hasBeenTrainedAtAll = False

    def addToTrainingData(self, inp, ans):
        """Given an input, and the correct output, add to the stored training data.

        :param np.array inp: np array of shape self.inputShape, a single sample
        :param string ans: the correct classification of the given sample ("up",
            "right", "down", or "left")
        """
        self.trainingInputs = np.vstack((self.trainingInputs, inp))
        self.trainingAnswers = np.append(self.trainingAnswers, ans)
        self.isNewDataSinceLastTrained = True

    def train(self):
        """Given the current built-up training data, fit our model to that data so it is
        prepared to start decoding measurements into game commands.
        """
        try:
            self.svmModel.fit(self.trainingInputs, self.trainingAnswers)
        except ValueError as e:
            print(f"Error while fitting model: {e}")
            return
        self.isNewDataSinceLastTrained = False
        self.hasBeenTrainedAtAll = True

    def decode(self, measurements):
        """Given measurements of the player, predict what that player is trying to do in
        the game and thus output a game command.

        :param np.array measurements: same structure as Player.measurements

        :return dict gameCommand: see WebSocket API of the game for how to structure
            commands (except without "timestring")
        """
        if not self.hasBeenTrainedAtAll:
            return None

        inp = np.array([measurements])
        (ans,) = self.svmModel.predict(inp)

        movement = {
            "up": {"x": 0, "y": 1},
            "right": {"x": 1, "y": 0},
            "down": {"x": 0, "y": -1},
            "left": {"x": -1, "y": 0},
        }[ans]

        gameCommand = {
            "move": movement,
        }
        return gameCommand
