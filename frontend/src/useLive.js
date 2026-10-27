import { useEffect, useState } from "react";
import { WS_URL } from "./api";

// Keeps the active task and pending confirmation in sync with the backend, reconnecting if needed.
export function useLive() {
  const [live, setLive] = useState({ active: null, awaiting: null, connected: false });

  useEffect(() => {
    let socket = null;
    let timer = null;
    let closed = false;

    const connect = () => {
      socket = new WebSocket(WS_URL);
      socket.onopen = () => setLive((s) => ({ ...s, connected: true }));
      socket.onmessage = (ev) => {
        const data = JSON.parse(ev.data);
        setLive((s) => ({ ...s, ...data, connected: true }));
      };
      socket.onclose = () => {
        setLive((s) => ({ ...s, connected: false }));
        if (!closed) timer = setTimeout(connect, 1000);
      };
    };
    connect();
    return () => {
      closed = true;
      clearTimeout(timer);
      if (socket) socket.close();
    };
  }, []);

  return live;
}
