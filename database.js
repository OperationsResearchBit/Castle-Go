// TODO: replace these with your own Supabase project's URL and anon/public key
const SUPABASE_URL = "https://pnwxqyjxjzepbfyhrdpo.supabase.co";
const SUPABASE_KEY = "sb_publishable_TtfzT97UwdAoPAcN3uxReA_Cbo7wzHe";

const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

let myColor = null;
let myName = "";
let lobbyCode = "";
let lobbyRowId = null;

async function joinGame() {
    const name = document.getElementById("username_input").value.trim().toUpperCase();
    const lobby = document.getElementById("lobby_input").value.trim().toUpperCase();
    if (!name || !lobby) return alert("Ruler Name and Lobby Match Code are required fields!");

    if (!window.pyCreateInitialState) {
        return alert("Game engine still loading. Please wait a moment and try again.");
    }

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
    supabaseClient.channel('match-' + lobbyRowId)
        .on('postgres_changes', {
            event: 'UPDATE',
            schema: 'public',
            table: 'castle_go_matches',
            filter: `id=eq.${lobbyRowId}`
        }, (payload) => {
            window.pyRenderState(JSON.stringify(payload.new.state), myColor, myName);
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
    supabaseClient.channel('leaderboard-updates')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'castle_go_results' }, () => {
            fetchLeaderboard();
        }).subscribe();
}
