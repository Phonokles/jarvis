const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('jarvis', {
  onState: (cb) => ipcRenderer.on('jarvis-state', (_, data) => cb(data)),
  minimize: () => ipcRenderer.send('window-minimize'),
  close: () => ipcRenderer.send('window-close'),
  quit: () => ipcRenderer.send('window-quit')
})
