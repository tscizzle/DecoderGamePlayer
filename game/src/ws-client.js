let ws = null;
let reconnectTimerId = null;

export const connect = ({ host, port, onmessage }) => {
  ws = new WebSocket(`ws://${host}:${port}`);

  ws.onopen = (ev) => {
    // When socket opens, stop attempting reconnect.
    if (reconnectTimerId) {
      clearInterval(reconnectTimerId);
      reconnectTimerId = null;
    }
  };

  if (onmessage) {
    ws.onmessage = onmessage;
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
