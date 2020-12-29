import os
import json
from datetime import datetime
import code

from player import LOG_FILE_PATH
from decoder import Decoder


def getLatestLogFile():
    """Get the latest log file (usually today's log file) in our log folder.

    :return str fileName: E.g. "2020-12-29.txt"
    """
    logDirName = os.path.dirname(LOG_FILE_PATH)
    fileNames = os.listdir(logDirName)
    # Our log files are named in the format "YYYY-MM-DD.txt" so later dates are greater
    # strings according to Python.
    logFileNames = [f for f in fileNames if f.endswith(".txt")]
    latestLogFileName = max(logFileNames)
    latestLogFilePath = os.path.join(logDirName, latestLogFileName)
    return latestLogFilePath


def main():
    # Get the latest log file.
    latestLogFile = getLatestLogFile()
    # Read the last line of the file to see the playerId of the latest run.
    with open(latestLogFile, "r") as f:
        for line in f:
            pass
        lastLog = json.loads(line)
        latestPlayerId = lastLog["playerId"]
    # Load from the file all the data for the latest run.
    with open(latestLogFile, "r") as f:
        logs = []
        for line in f:
            log = json.loads(line)
            if log["playerId"] == latestPlayerId:
                logs.append(log)

    # Create and train a decoder on the data from the log file.
    inputShape = (len(logs[0]["measurements"]),)
    decoder = Decoder(inputShape)
    for log in logs:
        if log["gameState"]["isCalibrating"]:
            decoder.addToTrainingData(log["measurements"], log["direction"])
    decoder.train()

    # Put the user into an interactive console, to play with the decoder and data.
    code.interact(local=dict(locals(), **globals()))


if __name__ == "__main__":
    main()
