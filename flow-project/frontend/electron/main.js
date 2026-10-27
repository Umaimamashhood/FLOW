// Electron main process: starts the backend, opens the window and the player windows, and registers the abort hotkey.
const { app, BrowserWindow, globalShortcut, session } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

// Let the player window start videos with sound without a click (the app is the one trusted to do this).
app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");

const BACKEND_URL = "http://127.0.0.1:8765";
const DEV_URL = "http://localhost:5173";
let backend = null;
let win = null;
const players = new Set();

function startBackend() {
  if (app.isPackaged) {
    const exe = path.join(process.resourcesPath, "backend", "flow-backend.exe");
    backend = spawn(exe, [], { stdio: "ignore", windowsHide: true });
  } else {
    const python = process.env.FLOW_PYTHON || "python";
    backend = spawn(python, ["-m", "flow"], {
      cwd: path.join(__dirname, "..", "..", "backend"),
      stdio: "inherit",
    });
  }
  backend.on("error", (err) => console.error("Backend failed to start:", err.message));
}

function createWindow() {
  win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "FLOW",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  if (app.isPackaged) {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  } else {
    win.loadURL(DEV_URL);
  }
}

// Open each video the backend asks for in its own player window, where it plays with sound.
function openPlayer(url) {
  const player = new BrowserWindow({
    width: 960,
    height: 600,
    title: "FLOW Player",
    autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  players.add(player);
  player.on("closed", () => players.delete(player));
  player.loadURL(url);
}

async function pollMedia() {
  try {
    const res = await fetch(`${BACKEND_URL}/media/pending`);
    const body = await res.json();
    for (const url of body.urls || []) openPlayer(url);
  } catch {
    // The backend is not running yet; the next poll will try again.
  }
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_wc, permission, callback) => {
    callback(permission === "media");
  });
  startBackend();
  createWindow();
  setInterval(pollMedia, 1500);
  globalShortcut.register("CommandOrControl+Shift+Escape", async () => {
    try {
      await fetch(`${BACKEND_URL}/abort`, { method: "POST" });
    } catch (err) {
      console.error("Abort failed:", err.message);
    }
  });
});

app.on("will-quit", () => {
  globalShortcut.unregisterAll();
  if (backend) backend.kill();
});

app.on("window-all-closed", () => app.quit());
