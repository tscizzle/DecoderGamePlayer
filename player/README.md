# DecoderGamePlayer | Player

## WebSocket API

This player has a WebSocket server which the game's WebSocket client connects to in order to send it game updates and receive game commands.

All messages are JSON, with fields `"TYPE"` and `"PAYLOAD"`.

- `"TYPE"` is a string that indicates what to do (e.g. `"START_GAME"`)
- `"PAYLOAD"` provides an object of additional parameters (e.g. `{"targetColor": "white"}`). The schema of `"PAYLOAD"` depends on the `"TYPE"`.

### Out

#### `"GAME_COMMAND"`

See `game/README.md`.

### In

#### `"GAME_UPDATE"`

See `game/README.md`.
