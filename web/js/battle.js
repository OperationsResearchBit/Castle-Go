// battle.js: load next to index.html with <script src="battle.js"></script>

// Local dev:   ws://127.0.0.1:8000/ws
// Codespaces:  wss://<codespace-name>-8000.app.github.dev/ws  (set port 8000 to Public)
// Production:  wss://your-server.example.com/ws
// Don't auto-detect "localhost": a Capacitor app also reports localhost.
const SERVER_URL = "ws://127.0.0.1:8000/ws";

const Battle = {
  socket: null,
  me: null,          // { id, name, seat, team }
  players: [],       // everyone in the current match
  mode: "1v1",

  // ---- hooks: assign these from your game code ----------------------------
  onStatus(text) {},                        // update the "Searching..." label
  onMatchStart(info) {},                    // { me, players, mode }: show the board
  onState(state) {},                        // redraw the board from server state
  onGameOver(winnerTeam, didWin) {},        // show the result screen
  onError(message) {},

  // ---- connection ---------------------------------------------------------
  connect() {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(SERVER_URL);
      this.socket.onopen = () => resolve();
      this.socket.onerror = () => reject(new Error("Could not reach server"));
      this.socket.onmessage = (event) => this._handle(JSON.parse(event.data));
      this.socket.onclose = () => this.onStatus("Disconnected");
    });
  },

  _send(payload) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(payload));
    }
  },

  // ---- actions your UI calls ----------------------------------------------
  async battle(mode, name) {
    this.mode = mode;
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.onStatus("Connecting...");
      await this.connect();
    }
    this.onStatus("Searching for opponents...");
    this._send({ type: "queue", mode, name });
  },

  cancel() {
    this._send({ type: "cancel" });
  },

  sendMove(move) {
    this._send({ type: "move", move });
  },

  // ---- incoming messages --------------------------------------------------
  _handle(message) {
    switch (message.type) {
      case "queued":
        this.onStatus("Searching...");
        break;
      case "queue_cancelled":
        this.onStatus("");
        break;
      case "match_found":
        this.me = message.you;
        this.players = message.players;
        this.onMatchStart({ me: this.me, players: this.players, mode: message.mode });
        break;
      case "state":
        this.onState(message.state);
        break;
      case "game_over":
        this.onGameOver(message.winner_team, message.winner_team === this.me.team);
        break;
      case "error":
        this.onError(message.message);
        break;
    }
  },
};
