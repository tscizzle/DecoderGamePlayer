from datetime import datetime, timezone


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
            "timestring": datetime.now(tz=timezone.utc).isoformat(),
        }
        return gameCommand
