let ws = null;

export const connect = ({ host, port, handleMessage }) => {
  console.info("Attempting connection to player ws server...");
  ws = new WebSocket(`ws://${host}:${port}`);

  ws.onopen = () => {
    console.info("Connection to player ws server opened.");
  };

  if (handleMessage) {
    ws.onmessage = (event) => {
      const msgObj = JSON.parse(event.data);
      handleMessage(msgObj);
    };
  }

  ws.onclose = () => {
    console.info("Connection to player ws server closed.");
    connect({ host, port, onmessage });
  };
};

export const send = (...args) => {
  if (ws && ws.readyState === 1) {
    ws.send(...args);
  }
};
