# DecoderGamePlayer | Player

## WebSocket API

This player has a WebSocket server which the game's WebSocket client connects to in order to send it game updates and receive game commands.

All messages are JSON, with fields `"TYPE"` and `"PAYLOAD"`.

- `"TYPE"` is a string that indicates what to do (e.g. `"START_GAME"`)
- `"PAYLOAD"` provides an object of additional parameters (e.g. `{"targetColor": "white"}`). The schema of `"PAYLOAD"` depends on the `"TYPE"`.

### Out

#### `"GAME_COMMAND"`

See `game/README.md`.

#### `"RESULT_OF_EVAL"`

In response to the `"PYTHON_CODE"` message documented below, Player sends this message back to the inspector, with the result of the code (the string representation of the result of the expression, or the traceback in case of an exception).

`"PAYLOAD"` has the following structure:

```
{
    "result": "30"
}
```

### In

#### `"GAME_UPDATE"`

See `game/README.md`.

#### `"PYTHON_CODE"`

A message from the inspector script to allow evaluating Python expressions while the Player coroutines are paused, to help inspect internal variables for fun and debug purposes.

If the Player coroutines are not already paused, receiving this message pauses them first. Resume the Player coroutines by sending the code `self.unpause()`.

`"PAYLOAD"` has the following structure:

```
{
    "pythonCode": "len(self.historicalMeasurements)"
}
```
