# DecodeGamePlayer

Parent repo for the DecodeGamePlayer system.

Contains multiple standalone components, each with their own well-defined API.

- Game
- Player
- Decoder

Game accepts inputs and outputs game info. In that way, it can be played by a person, or bots can be built to learn how to play the game.

Player is a fake player who accepts game info and outputs fake measurements (imagine someone watching a game and their brain neurons firing and being measured).

Decoder reads the player's measurements and tries to decode them into inputs for the game, learning how to do so over time (if a certain measurement is very high whenever the game info says moving left will result in a win, then the decoder should learn that that measurement being high indicates the player is trying to move left).
