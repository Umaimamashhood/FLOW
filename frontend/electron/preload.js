// Deliberately minimal: the renderer talks to the backend over HTTP and WebSocket on localhost.
const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("flow", { platform: process.platform });
