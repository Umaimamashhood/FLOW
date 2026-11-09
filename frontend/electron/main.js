// Electron main process: starts the Python backend, opens the window, registers the global abort hotkey.
const { app, BrowserWindow, globalShortcut, session } = require("electron");
const { spawn } = require("child_process");
const path = require("path");

const BACKEND_URL = "http://127.0.0.1:8765";
const DEV_URL = "http://localhost:5173";
let backend = null;
let win = null;

function startBackend() {
  if (app.isPackaged) {
    // Packaged build: PyInstaller executable shipped under resources/backend
    const exe = path.join(process.resourcesPath, "backend", "flow-backend.exe");
    backend = spawn(exe, [], { stdio: "ignore", windowsHide: true });
  } else {
    // Development: run the backend from the source tree
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

app.whenReady().then(() => {
  // Only the microphone is granted to the renderer (push-to-talk).
  session.defaultSession.setPermissionRequestHandler((_wc, permission, callback) => {
    callback(permission === "media");
  });
  startBackend();
  createWindow();
  // Global abort hotkey (SRS FR-5, P-10): works even when FLOW is not focused.
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
