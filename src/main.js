const { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const WebSocket = require('ws')
const http = require('http')

let win, tray, wss
let ollamaProcess, jarvisProcess
let wsClient = null

const JARVIS_DIR = path.join(require('os').homedir(), 'ki', 'jarvis')
const VENV_PYTHON = path.join(JARVIS_DIR, 'venv', 'bin', 'python')
const WS_PORT = 6789

function createWindow() {
  win = new BrowserWindow({
    width: 480,
    height: 680,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: false,
    skipTaskbar: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '..', 'assets', 'icon.png')
  })

  win.loadFile(path.join(__dirname, 'index.html'))

  win.on('closed', () => { win = null })
}

function createTray() {
  const icon = nativeImage.createFromPath(path.join(__dirname, '..', 'assets', 'icon.png'))
  tray = new Tray(icon.resize({ width: 16, height: 16 }))
  const menu = Menu.buildFromTemplate([
    { label: 'Show JARVIS', click: () => win?.show() },
    { label: 'Quit', click: () => { cleanup(); app.quit() } }
  ])
  tray.setContextMenu(menu)
  tray.setToolTip('JARVIS')
  tray.on('click', () => win?.show())
}

function startWebSocketServer() {
  wss = new WebSocket.Server({ port: WS_PORT })
  wss.on('connection', (ws) => {
    console.log('[WS] Python connected')
    wsClient = ws
    ws.on('message', (msg) => {
      try {
        const data = JSON.parse(msg)
        win?.webContents.send('jarvis-state', data)
      } catch (e) {}
    })
    ws.on('close', () => { wsClient = null })
  })
  console.log(`[WS] Server running on port ${WS_PORT}`)
}

function waitForOllama(retries, cb) {
  const req = http.get('http://localhost:11434', (res) => cb(null))
  req.on('error', () => {
    if (retries <= 0) return cb(new Error('Ollama timeout'))
    setTimeout(() => waitForOllama(retries - 1, cb), 1000)
  })
  req.end()
}

function startOllama() {
  return new Promise((resolve) => {
    // Check if already running
    waitForOllama(2, (err) => {
      if (!err) { console.log('[Ollama] Already running'); return resolve() }

      console.log('[Ollama] Starting...')
      win?.webContents.send('jarvis-state', { state: 'booting', msg: 'Starting Ollama...' })

      ollamaProcess = spawn('ollama', ['serve'], {
        detached: false,
        stdio: 'ignore',
        env: { ...process.env }
      })

      waitForOllama(30, (err) => {
        if (err) console.error('[Ollama] Failed to start:', err)
        else console.log('[Ollama] Ready')
        resolve()
      })
    })
  })
}

function startJarvis() {
  console.log('[Jarvis] Starting Python backend...')
  win?.webContents.send('jarvis-state', { state: 'booting', msg: 'Loading JARVIS...' })

  jarvisProcess = spawn(VENV_PYTHON, ['main.py'], {
    cwd: JARVIS_DIR,
    env: {
      ...process.env,
      JARVIS_WS_PORT: String(WS_PORT)
    },
    stdio: ['ignore', 'pipe', 'pipe']
  })

  jarvisProcess.stdout.on('data', (d) => process.stdout.write('[PY] ' + d))
  jarvisProcess.stderr.on('data', (d) => process.stderr.write('[PY] ' + d))
  jarvisProcess.on('exit', (code) => {
    console.log('[Jarvis] Process exited:', code)
    win?.webContents.send('jarvis-state', { state: 'error', msg: 'JARVIS process stopped.' })
  })
}

function cleanup() {
  jarvisProcess?.kill()
  ollamaProcess?.kill()
}

ipcMain.on('window-minimize', () => win?.minimize())
ipcMain.on('window-close', () => { win?.hide() })
ipcMain.on('window-quit', () => { cleanup(); app.quit() })

app.whenReady().then(async () => {
  createWindow()
  createTray()
  startWebSocketServer()

  await startOllama()
  startJarvis()
})

app.on('window-all-closed', (e) => e.preventDefault())
app.on('before-quit', cleanup)
