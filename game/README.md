# DecoderGamePlayer | Game

## WebSocket API

This game establishes a WebSocket connection with the player's WebSocket server in order to send it game state updates, as well as receive commands from it to play this game.

All messages are JSON, with fields `"TYPE"` and `"PAYLOAD"`.

- `"TYPE"` is a string that indicates what to do (e.g. `"START_GAME"`)
- `"PAYLOAD"` provides an object of additional parameters (e.g. `{"targetColor": "white"}`). The schema of `"PAYLOAD"` depends on the `"TYPE"`.

### In

#### `"GAME_COMMAND"`

Our Player code sends WebSocket messages of this TYPE in order the play the game (in contrast to when the game is played by a human and they use the physical keyboard to provide input).

`"PAYLOAD"` has the following structure:

```
{
    "move": {
        "x": 2,
        "y": 5,
    },
    "timestring": "2020-11-18T09:59:45.123+00:00"
}
```

### Out

#### `"GAME_UPDATE"`

A snapshot of the state of this game. The info in this snapshot should fully describe the game.

`"PAYLOAD"` has the following structure:

```
{
    "gameState": {
        "playerCursor": {
            "x": 2,
            "y": 5,
            "radius": 20
        },
        "target": {
            "x": 3,
            "y": 6,
            "radius": 20
        },
    }
}
```
