const vscode = require("vscode");

class LocalAuthProvider {
  constructor() {
    this._onDidChangeSessions = new vscode.EventEmitter();
    this.onDidChangeSessions = this._onDidChangeSessions.event;
    this.currentSession = {
      id: "extrace-local-session",
      accessToken: "extrace-local-token",
      account: {
        id: "extrace-local-account",
        label: "ExTrace Local Account",
      },
      scopes: ["default"],
    };
  }

  getSessions() {
    return Promise.resolve([this.currentSession]);
  }

  createSession(scopes) {
    this.currentSession = {
      ...this.currentSession,
      scopes,
    };
    this._onDidChangeSessions.fire();
    return Promise.resolve(this.currentSession);
  }

  removeSession() {
    this._onDidChangeSessions.fire();
    return Promise.resolve();
  }
}

class LocalFileSystemProvider {
  constructor() {
    this._onDidChangeFile = new vscode.EventEmitter();
    this.onDidChangeFile = this._onDidChangeFile.event;
  }

  stat() {
    return {
      ctime: Date.now(),
      mtime: Date.now(),
      size: 7,
      type: vscode.FileType.File,
    };
  }

  readDirectory() {
    return [];
  }

  createDirectory() {}

  readFile() {
    return Buffer.from("extrace");
  }

  writeFile(uri) {
    this._emitChanged(uri);
  }

  delete(uri) {
    this._emitDeleted(uri);
  }

  rename(oldUri, newUri) {
    this._emitDeleted(oldUri);
    this._emitChanged(newUri);
  }

  watch() {
    return new vscode.Disposable(() => {});
  }

  _emitChanged(uri) {
    this._onDidChangeFile.fire([
      { type: vscode.FileChangeType.Changed, uri },
    ]);
  }

  _emitDeleted(uri) {
    this._onDidChangeFile.fire([
      { type: vscode.FileChangeType.Deleted, uri },
    ]);
  }
}

module.exports = {
  LocalAuthProvider,
  LocalFileSystemProvider,
};
