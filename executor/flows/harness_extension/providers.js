const vscode = require("vscode");

class LocalAuthProvider {
  constructor() {
    this.onDidChangeSessions = new vscode.EventEmitter();
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
    return Promise.resolve(this.currentSession);
  }

  removeSession() {
    return Promise.resolve();
  }
}

class LocalFileSystemProvider {
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

  writeFile() {}

  delete() {}

  rename() {}

  watch() {
    return new vscode.Disposable(() => {});
  }
}

module.exports = {
  LocalAuthProvider,
  LocalFileSystemProvider,
};
