# DecoderGamePlayer | Game

## WebSocket API

This game establishes a WebSocket connection with the player's WebSocket server in order to send it game state updates, as well as a WebSocket connection with the decoder's WebSocket server in order to receive commands from it to play this game.

All messages are JSON, with fields `"TYPE"` and `"PAYLOAD"`.

- `"TYPE"` is a string that indicates what to do (e.g. `"keypress"`)
- `"PAYLOAD"` provides an object of additional parameters (e.g. `{"key": "right_arrow"}`). The schema of `"PAYLOAD"` depends on the `"TYPE"`.

### In

#### `"KEYPRESS"`

### Out

#### `"GAME_UPDATE"`

A snapshot of the state of this game. The info in this snapshot should fully describe the game.

`"PAYLOAD"` has the following structure:

```
{
    "gameState": {
        "cursorPosition": { "x": 2, "y": 5 }
    }
}
```
