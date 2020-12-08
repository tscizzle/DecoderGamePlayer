import json
import asyncio
import time

import websockets
import websockets.exceptions

import player


async def REPL():
    """Display a prompt to type, send entered code to Player, and display the code
    result sent back from Player.
    """
    loop = asyncio.get_event_loop()
    uri = f"ws://{player.HOST}:{player.PORT}"
    while True:
        try:
            print("Attempting WebSocket connection...")
            async with websockets.connect(uri) as websocket:
                print("WebSocket connect open.")
                while True:
                    # Without run_in_executor(), just plain input() hinders pinging that
                    # the websockets library does, causing connection errors.
                    pythonCode = await loop.run_in_executor(None, lambda: input(">>> "))
                    # If nothing was typed, do nothing.
                    if not pythonCode:
                        continue
                    msgDict = {
                        "TYPE": "PYTHON_CODE",
                        "PAYLOAD": {"pythonCode": pythonCode},
                    }
                    msg = json.dumps(msgDict)
                    try:
                        await websocket.send(msg)
                        resultMsg = await websocket.recv()
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket connection closed.")
                        break
                    resultMsgDict = json.loads(resultMsg)
                    assert resultMsgDict["TYPE"] == "RESULT_OF_EVAL"
                    result = resultMsgDict["PAYLOAD"]["result"]
                    print(result)
        except ConnectionRefusedError:
            print(f"Unable to connect to {uri}.")
            time.sleep(1)


def main():
    try:
        asyncio.run(REPL())
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt...")


if __name__ == "__main__":
    main()
