// Modules to control application life and create native browser window
const path = require('path');
const { app, BrowserWindow, Menu, ipcMain } = require('electron')
const iconPath = path.join(__dirname, "web", "public", "icon.ico");

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 1024,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath
  })

  // and load the index.html of the app.
  mainWindow.loadURL('http://localhost:8000/templates/app.html');

  mainWindow.setMinimumSize(1024, 1024);
  // Open the DevTools.
  // mainWindow.webContents.openDevTools()

  // Emitted when the window is closed.
  mainWindow.on('closed', function () {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    mainWindow = null
  })
}

let terminalWindow

function createTerminalWindow() {
  // Create the browser window.
  terminalWindow = new BrowserWindow({
    width: 512,
    height: 256,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath
  })
  terminalWindow.removeMenu();
  terminalWindow.setMinimumSize(300, 150);

  terminalWindow.loadURL('http://localhost:8000/templates/terminal.html');
}

let viewWindow;
let pendingViewMessage = null;

function createViewWindow(windowName) {
  // Create the browser window.
  viewWindow = new BrowserWindow({
    title: `Viewing ${windowName}`,
    width: 800,
    height: 1024,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: iconPath,
    show: false
  })

  viewWindow.loadURL('http://localhost:8000/templates/view.html');

  viewWindow.on('closed', () => {
    viewWindow = null
  })

  viewWindow.webContents.on('did-finish-load', function () {
    viewWindow.show();

    if (pendingViewMessage) {
      setTimeout(() => {
        viewWindow.webContents.send('receive-message', pendingViewMessage);
        pendingViewMessage = null;
      }, 500);
    }
  });

}

ipcMain.on('message-to-view', (event, data) => {
  pendingViewMessage = data;

  if (viewWindow) {
    viewWindow.webContents.send('receive-message', data)
  }
})

ipcMain.on('message-to-main', (event, data) => {
  if (mainWindow) {
    mainWindow.webContents.send('receive-message', data)
  }
})

ipcMain.on('open-view-window', (event, data)  => {
  if (!viewWindow) {
    createViewWindow(data);
  }
})

const menuTemplate = [
  {
    label: 'File',
    submenu: [
      { role: 'quit' },
    ],
  },
  {
    label: 'Edit',
    submenu: [
      { role: 'undo' },
      { role: 'redo' },
      { type: 'separator' },
      { role: 'cut' },
      { role: 'copy' },
      { role: 'paste' },
    ],
  },
  {
    label: 'View',
    submenu: [
      { role: 'reload' },
      { role: 'toggledevtools' },
      { type: 'separator' },
      { role: 'resetzoom' },
      { role: 'zoomin' },
      { role: 'zoomout' },
      { type: 'separator' },
      { role: 'togglefullscreen' },
    ],
  },
  {
    label: 'Tools',
    submenu: [
      {
        label: 'Terminal',
        click() {
          createTerminalWindow();
        },
      },
    ],
  },
  {
    label: 'Help',
    submenu: [
      {
        label: 'Learn More',
        click() {
          require('electron').shell.openExternal('https://s2aulendo.github.io/HeatCompensation-Docs/');
        },
      },
    ],
  },
];

const menu = Menu.buildFromTemplate(menuTemplate);
Menu.setApplicationMenu(menu);

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow)

// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', function () {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) createWindow()
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
