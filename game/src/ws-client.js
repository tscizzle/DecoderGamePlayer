let ws = null;
let reconnectTimerId = null;

export const connect = ({ host, port, handleMessage }) => {
  ws = new WebSocket(`ws://${host}:${port}`);

  ws.onopen = (ev) => {
    // When socket opens, stop attempting reconnect.
    if (reconnectTimerId) {
      clearInterval(reconnectTimerId);
      reconnectTimerId = null;
    }
  };

  if (handleMessage) {
    ws.onmessage = (event) => {
      const msgObj = JSON.parse(event.data);
      handleMessage(msgObj);
    };
  }

  ws.onclose = (ev) => {
    // When socket closes, begin periodically attempting reconnect.
    reconnectTimerId = setInterval(
      () => connect({ host, port, onmessage }),
      5000
    );
  };
};

export const send = (...args) => {
  if (ws && ws.readyState === 1) {
    ws.send(...args);
  }
};
