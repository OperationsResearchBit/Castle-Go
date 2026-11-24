// ============================================================
// Castle Go — Premium entitlement layer
// ------------------------------------------------------------
// NOTE: this is a lightweight, CLIENT-ONLY flag for prototyping the
// premium feature set (expansions/maps, colors & avatars, full-screen,
// ad-free play, replays, Conquest Mode). It is NOT secure — anyone can
// flip it via devtools/localStorage. Before shipping, wire setPremium()
// up to a real entitlement check (e.g. a Supabase `profiles` table
// populated by a Stripe webhook, checked server-side / via RLS) rather
// than trusting this flag on its own.
// ============================================================

const PREMIUM_KEY = "castlego_premium";
const CAMPAIGN_KEY = "castlego_campaign_progress";
const COLOR_PREF_KEY = "castlego_color_pref";
const AVATAR_PREF_KEY = "castlego_avatar_pref";

const AVATAR_OPTIONS = ["🐺", "🦁", "🐉", "🦅", "🐴", "👑", "🛡️", "⚔️", "🦉", "🐗"];

function isPremium() {
    return localStorage.getItem(PREMIUM_KEY) === "true";
}

function setPremium(value) {
    localStorage.setItem(PREMIUM_KEY, value ? "true" : "false");
    applyPremiumUI();
}

function togglePremium() {
    setPremium(!isPremium());
}

function applyPremiumUI() {
    const premium = isPremium();

    document.querySelectorAll(".premium-only").forEach(el => {
        el.classList.toggle("hidden", !premium);
    });
    document.querySelectorAll(".free-only").forEach(el => {
        el.classList.toggle("hidden", premium);
    });

    const statusEl = document.getElementById("premium_status_label");
    if (statusEl) statusEl.innerText = premium ? "💎 Premium Active" : "Free Plan";

    const toggleBtn = document.getElementById("premium_toggle_btn");
    if (toggleBtn) toggleBtn.innerText = premium ? "Deactivate Premium (Demo)" : "Activate Premium (Demo)";

    // Lock premium-only options inside map <select> elements
    document.querySelectorAll("select.map-select").forEach(sel => {
        Array.from(sel.options).forEach(opt => {
            if (opt.dataset.premium === "true" && !premium) {
                opt.disabled = true;
                if (!opt.textContent.includes("🔒")) opt.textContent += " 🔒";
            } else {
                opt.disabled = false;
                opt.textContent = opt.textContent.replace(" 🔒", "");
            }
        });
        if (sel.selectedOptions[0] && sel.selectedOptions[0].disabled) {
            sel.value = "classic";
        }
    });

    document.querySelectorAll(".color-input").forEach(inp => { inp.disabled = !premium; });
    document.querySelectorAll(".avatar-grid button").forEach(btn => { btn.disabled = !premium; });
}

function buildAvatarGrid(containerId, hiddenInputId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = "";
    container.className = "avatar-grid grid grid-cols-5 gap-1";
    const saved = getSavedAvatarPref();
    AVATAR_OPTIONS.forEach(emoji => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.textContent = emoji;
        btn.className = "py-1 rounded-lg bg-gray-800 border border-gray-700 hover:border-cyan-500 text-lg transition disabled:opacity-40 disabled:cursor-not-allowed";
        if (emoji === saved) {
            btn.classList.add("border-cyan-400", "bg-cyan-900/40");
        }
        btn.onclick = () => {
            document.getElementById(hiddenInputId).value = emoji;
            container.querySelectorAll("button").forEach(b => b.classList.remove("border-cyan-400", "bg-cyan-900/40"));
            btn.classList.add("border-cyan-400", "bg-cyan-900/40");
            localStorage.setItem(AVATAR_PREF_KEY, emoji);
        };
        container.appendChild(btn);
    });
    if (saved) {
        const input = document.getElementById(hiddenInputId);
        if (input) input.value = saved;
    }
}

function getSavedColorPref() {
    return localStorage.getItem(COLOR_PREF_KEY) || "";
}
function saveColorPref(hex) {
    localStorage.setItem(COLOR_PREF_KEY, hex);
}
function getSavedAvatarPref() {
    return localStorage.getItem(AVATAR_PREF_KEY) || "";
}

// ---- Conquest Mode progress ----
function getCampaignProgress() {
    try {
        return JSON.parse(localStorage.getItem(CAMPAIGN_KEY) || "{}");
    } catch (e) {
        return {};
    }
}
function markCampaignLevelComplete(levelId) {
    const progress = getCampaignProgress();
    progress[levelId] = true;
    localStorage.setItem(CAMPAIGN_KEY, JSON.stringify(progress));
}

document.addEventListener("DOMContentLoaded", applyPremiumUI);
