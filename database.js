// TODO: replace these with your own Supabase project's URL and anon/public key
const SUPABASE_URL = "https://pnwxqyjxjzepbfyhrdpo.supabase.co";
const SUPABASE_KEY = "sb_publishable_TtfzT97UwdAoPAcN3uxReA_Cbo7wzHe";

const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

let myColor = null;
let myName = "";
let lobbyCode = "";
let lobbyRowId = null;
let isSpectating = false;

let matchChannel = null;
let leaderboardChannel = null;
let activeGamesChannel = null;

function cleanupMatchSubscriptions() {
    if (matchChannel) {
        supabaseClient.removeChannel(matchChannel);
        matchChannel = null;
    }
    if (leaderboardChannel) {
        supabaseClient.removeChannel(leaderboardChannel);
        leaderboardChannel = null;
    }
}

async function joinGame() {
    const name = document.getElementById("username_input").value.trim().toUpperCase();
    const lobby = document.getElementById("lobby_input").value.trim().toUpperCase();
    if (!name || !lobby) return alert("Ruler Name and Lobby Match Code are required fields!");

    if (!window.pyCreateInitialState) {
        return alert("Game engine still loading. Please wait a moment and try again.");
    }

    cleanupMatchSubscriptions();
    isSpectating = false;

    const { data: rows, error: selErr } = await supabaseClient
        .from('castle_go_matches')
        .select('*')
        .eq('lobby_code', lobby);

    if (selErr) return alert("Supabase error (no tables?): " + selErr.message);

    let row;

    if (!rows || rows.length === 0) {
        const initialStateJson = window.pyCreateInitialState(name);
        const { data, error } = await supabaseClient
            .from('castle_go_matches')
            .insert([{ lobby_code: lobby, state: JSON.parse(initialStateJson) }])
            .select();
        if (error) return alert("Supabase pipeline rejection: " + error.message);
        row = data[0];
        myColor = 'B';
    } else {
        row = rows[0];
        const state = row.state;
        if (state.players.B.name === name) {
            myColor = 'B';
        } else if (state.players.W.name === name) {
            myColor = 'W';
        } else if (!state.players.W.name) {
            state.players.W.name = name;
            const { data, error } = await supabaseClient
                .from('castle_go_matches')
                .update({ state: state })
                .eq('id', row.id)
                .select();
            if (error) return alert("Supabase pipeline rejection: " + error.message);
            row = data[0];
            myColor = 'W';
        } else {
            return alert("That lobby already has two rulers on the throne! Try a different lobby code.");
        }
    }

    myName = name;
    lobbyCode = lobby;
    lobbyRowId = row.id;

    document.getElementById("display_name_prefix").innerText = "Ruling as";
    document.getElementById("display_name").innerText = name;
    document.getElementById("display_room").innerText = lobby;
    document.getElementById("setup_screen").classList.add("hidden");
    document.getElementById("game_screen").classList.remove("hidden");

    window.pyRenderState(JSON.stringify(row.state), myColor, name);
    listenToMatch();
    fetchLeaderboard();
    listenToLeaderboard();
}

function listenToMatch() {
    matchChannel = supabaseClient.channel('match-' + lobbyRowId)
        .on('postgres_changes', {
            event: 'UPDATE',
            schema: 'public',
            table: 'castle_go_matches',
            filter: `id=eq.${lobbyRowId}`
        }, (payload) => {
            if (isSpectating) {
                window.pyWatchMatch(JSON.stringify(payload.new.state));
            } else {
                window.pyRenderState(JSON.stringify(payload.new.state), myColor, myName);
            }
        }).subscribe();
}

async function pushState(stateJson) {
    if (!lobbyRowId) return;
    await supabaseClient.from('castle_go_matches').update({ state: JSON.parse(stateJson) }).eq('id', lobbyRowId);
}

async function recordResult(resultJson) {
    const payload = JSON.parse(resultJson);
    payload.lobby_code = lobbyCode;
    const { error } = await supabaseClient.from('castle_go_results').insert([payload]);
    if (error) console.error("Could not record result:", error.message);
}

async function fetchLeaderboard() {
    const { data, error } = await supabaseClient
        .from('castle_go_results')
        .select('*')
        .order('finished_at', { ascending: false });

    if (error) return;

    const stats = {};
    const touch = (name) => {
        if (!name) return;
        if (!stats[name]) stats[name] = { wins: 0, played: 0 };
    };

    data.forEach(row => {
        touch(row.black_name);
        touch(row.white_name);
        if (row.black_name) stats[row.black_name].played += 1;
        if (row.white_name) stats[row.white_name].played += 1;
        if (row.winner_name && row.winner_name !== 'draw' && stats[row.winner_name]) {
            stats[row.winner_name].wins += 1;
        }
    });

    const ranked = Object.entries(stats).sort((a, b) => b[1].wins - a[1].wins);

    const list = document.getElementById("leaderboard_list");
    if (ranked.length === 0) {
        list.innerHTML = '<div class="text-gray-500 py-3 text-center">No completed matches yet.</div>';
        return;
    }

    list.innerHTML = "";
    ranked.forEach(([name, s], i) => {
        const medal = i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : "·";
        list.innerHTML += `
            <div class="grid grid-cols-3 py-2 text-xs items-center border-b border-gray-800/40">
                <span class="text-gray-300 truncate">${medal} ${name}</span>
                <span class="text-emerald-400 font-black text-right">${s.wins}</span>
                <span class="text-gray-500 text-right">${s.played}</span>
            </div>`;
    });
}

function listenToLeaderboard() {
    leaderboardChannel = supabaseClient.channel('leaderboard-updates')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'castle_go_results' }, () => {
            fetchLeaderboard();
        }).subscribe();
}

function leaveGame() {
    cleanupMatchSubscriptions();
    if (window.pyLeaveGame) window.pyLeaveGame();

    isSpectating = false;
    myColor = null;
    myName = "";
    lobbyCode = "";
    lobbyRowId = null;

    document.getElementById("game_screen").classList.add("hidden");
    document.getElementById("setup_screen").classList.remove("hidden");

    fetchActiveGames();
}

async function watchGame(row) {
    if (!window.pyWatchMatch) {
        return alert("Game engine still loading. Please wait a moment and try again.");
    }

    cleanupMatchSubscriptions();
    isSpectating = true;
    myColor = null;
    myName = "Spectator";
    lobbyCode = row.lobby_code;
    lobbyRowId = row.id;

    document.getElementById("display_name_prefix").innerText = "Spectating as";
    document.getElementById("display_name").innerText = "Spectator";
    document.getElementById("display_room").innerText = row.lobby_code;
    document.getElementById("setup_screen").classList.add("hidden");
    document.getElementById("game_screen").classList.remove("hidden");

    window.pyWatchMatch(JSON.stringify(row.state));
    listenToMatch();
    fetchLeaderboard();
    listenToLeaderboard();
}

async function fetchActiveGames() {
    const container = document.getElementById("active_games_list");
    if (!container) return;

    const { data, error } = await supabaseClient
        .from('castle_go_matches')
        .select('*')
        .order('id', { ascending: false })
        .limit(30);

    if (error) {
        container.innerHTML = '<div class="text-gray-500 text-xs py-3 text-center">Could not load live games.</div>';
        return;
    }

    const ongoing = (data || []).filter(row => row.state && !row.state.winner).slice(0, 12);

    if (ongoing.length === 0) {
        container.innerHTML = '<div class="text-gray-500 text-xs py-3 text-center">No live games right now.</div>';
        return;
    }

    container.innerHTML = "";
    ongoing.forEach(row => container.appendChild(buildGamePreviewCard(row)));
}

function buildGamePreviewCard(row) {
    const state = row.state;

    const wrap = document.createElement("div");
    wrap.className = "flex items-center gap-3 p-2 rounded-lg bg-gray-950 border border-gray-800 hover:border-cyan-500/50 transition cursor-pointer";
    wrap.onclick = () => watchGame(row);

    // Low-resolution 9x9 preview of the board — a quick colored-dot readout, not the full interactive board
    const grid = document.createElement("div");
    grid.className = "grid grid-cols-9 gap-[1px] bg-gray-900 p-1 rounded flex-shrink-0";
    grid.style.width = "54px";
    grid.style.height = "54px";
    for (let r = 0; r < 9; r++) {
        for (let c = 0; c < 9; c++) {
            const px = document.createElement("div");
            const owner = state.board[r][c];
            px.style.backgroundColor = owner === "B" ? "#f59e0b" : owner === "W" ? "#22d3ee" : "#1f2937";
            grid.appendChild(px);
        }
    }

    const info = document.createElement("div");
    info.className = "min-w-0 flex-1";

    const codeLine = document.createElement("div");
    codeLine.className = "text-xs font-mono text-cyan-400 font-bold truncate";
    codeLine.textContent = row.lobby_code;

    const bLine = document.createElement("div");
    bLine.className = "text-[11px] text-amber-300 truncate";
    bLine.textContent = "🟠 " + (state.players.B.name || "waiting...");

    const wLine = document.createElement("div");
    wLine.className = "text-[11px] text-cyan-300 truncate";
    wLine.textContent = "🟦 " + (state.players.W.name || "waiting...");

    const phaseLine = document.createElement("div");
    phaseLine.className = "text-[10px] text-gray-500 uppercase tracking-wide";
    phaseLine.textContent = state.phase === 1 ? "Phase 1: Maneuvers" : "Phase 2: Battle";

    info.appendChild(codeLine);
    info.appendChild(bLine);
    info.appendChild(wLine);
    info.appendChild(phaseLine);

    const watchBtn = document.createElement("div");
    watchBtn.className = "text-[10px] font-bold text-gray-500 uppercase tracking-wider flex-shrink-0";
    watchBtn.textContent = "Watch →";

    wrap.appendChild(grid);
    wrap.appendChild(info);
    wrap.appendChild(watchBtn);
    return wrap;
}

function listenToActiveGames() {
    activeGamesChannel = supabaseClient.channel('active-games-updates')
        .on('postgres_changes', { event: '*', schema: 'public', table: 'castle_go_matches' }, () => {
            fetchActiveGames();
        }).subscribe();
}

fetchActiveGames();
listenToActiveGames();
