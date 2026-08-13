"use strict";

const apiBaseInput = document.getElementById("apiBase");
const apiStatusDot = document.getElementById("apiStatus");

function apiBase() {
  return apiBaseInput.value.trim().replace(/\/$/, "");
}

async function api(path, options = {}) {
  const res = await fetch(apiBase() + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let data = null;
  try { data = await res.json(); } catch (_) { /* no body */ }
  if (!res.ok) {
    const detail = (data && data.detail) || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return data;
}

async function checkConnection() {
  try {
    await api("/leaderboard");
    apiStatusDot.className = "dot dot-ok";
    apiStatusDot.title = "接続OK";
  } catch (_) {
    apiStatusDot.className = "dot dot-err";
    apiStatusDot.title = "接続失敗";
  }
}
apiBaseInput.addEventListener("change", checkConnection);
checkConnection();

// ---------- toast ----------

let toastTimer = null;
function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = "toast" + (isError ? " err" : "");
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 3200);
}

// ---------- tabs ----------

const tabButtons = document.querySelectorAll(".tab-btn");
const views = document.querySelectorAll(".view");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    views.forEach((v) => v.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`view-${btn.dataset.view}`).classList.add("active");
    if (btn.dataset.view === "history") loadHistory();
    if (btn.dataset.view === "leaderboard") loadLeaderboard();
  });
});

// ---------- battle: create ----------

const matchForm = document.getElementById("matchForm");
const startBtn = document.getElementById("startBtn");
const battleStage = document.getElementById("battleStage");

let currentBattleId = null;
let hasVoted = false;

matchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = document.getElementById("questionInput").value.trim();
  const botA = document.getElementById("botA").value.trim();
  const botB = document.getElementById("botB").value.trim();
  if (!question || !botA || !botB) return;

  setStarting(true);
  try {
    const result = await api("/battles", {
      method: "POST",
      body: JSON.stringify({ question, bot_a: botA, bot_b: botB }),
    });
    currentBattleId = result.battle_id;
    hasVoted = false;
    renderBattle({
      question: result.question,
      bot_a: botA,
      bot_b: botB,
      response_a: result.response_a,
      response_b: result.response_b,
    });
    await refreshResult();
  } catch (err) {
    showToast(`対戦作成に失敗: ${err.message}`, true);
  } finally {
    setStarting(false);
  }
});

function setStarting(isLoading) {
  startBtn.disabled = isLoading;
  startBtn.querySelector(".btn-label").textContent = isLoading ? "対戦準備中…" : "対戦開始";
  startBtn.querySelector(".btn-spinner").hidden = !isLoading;
}

function renderBattle(b) {
  battleStage.hidden = false;
  document.getElementById("questionEcho").textContent = b.question;
  document.getElementById("nameA").textContent = b.bot_a;
  document.getElementById("nameB").textContent = b.bot_b;
  document.getElementById("responseA").textContent = b.response_a;
  document.getElementById("responseB").textContent = b.response_b;
  document.getElementById("voteMessage").textContent = "";
  document.getElementById("winnerBanner").hidden = true;
  document.querySelectorAll(".vote-btn").forEach((btn) => (btn.disabled = false));
  document.querySelectorAll(".fighter").forEach((f) => f.classList.remove("voted-for"));
  setVoteBars({ a: 0, b: 0, tie: 0 });
  battleStage.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- battle: voting ----------

document.querySelectorAll(".vote-btn").forEach((btn) => {
  btn.addEventListener("click", () => castVote(btn.dataset.choice));
});

async function castVote(choice) {
  if (!currentBattleId || hasVoted) return;
  const userId = document.getElementById("userId").value.trim() || "guest";

  try {
    const res = await api(`/battles/${currentBattleId}/vote`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, choice }),
    });
    hasVoted = true;
    setVoteBars(res.votes);
    document.querySelectorAll(".vote-btn").forEach((btn) => (btn.disabled = true));
    const votedFighter = document.querySelector(`.fighter[data-choice="${choice}"]`);
    if (votedFighter) votedFighter.classList.add("voted-for");
    document.getElementById("voteMessage").textContent = "投票を受け付けました。+1ポイント獲得。";
    showToast("投票完了");
    await refreshResult();
  } catch (err) {
    if (err.message.includes("already voted")) {
      hasVoted = true;
      document.querySelectorAll(".vote-btn").forEach((btn) => (btn.disabled = true));
      document.getElementById("voteMessage").textContent = "このIDは既に投票済みです。";
    } else {
      showToast(`投票に失敗: ${err.message}`, true);
    }
  }
}

function setVoteBars(votes) {
  const total = votes.a + votes.b + votes.tie;
  const pctA = total ? (votes.a / total) * 100 : 0;
  const pctB = total ? (votes.b / total) * 100 : 0;
  document.getElementById("barA").style.width = `${pctA}%`;
  document.getElementById("barB").style.width = `${pctB}%`;
  document.getElementById("countA").textContent = `${votes.a}票`;
  document.getElementById("countB").textContent = `${votes.b}票`;
  document.getElementById("countTie").textContent = `${votes.tie}票`;
}

async function refreshResult() {
  if (!currentBattleId) return;
  try {
    const result = await api(`/battles/${currentBattleId}`);
    setVoteBars({ a: result.votes_a, b: result.votes_b, tie: result.votes_tie });
    const banner = document.getElementById("winnerBanner");
    if (result.winner) {
      const label =
        result.winner === "a" ? `🏆 ${result.bot_a} の勝利`
        : result.winner === "b" ? `🏆 ${result.bot_b} の勝利`
        : "🤝 引き分け";
      banner.textContent = label;
      banner.hidden = false;
    } else {
      banner.hidden = true;
    }
  } catch (_) { /* サイレントに無視 */ }
}

// ---------- history ----------

async function loadHistory() {
  const container = document.getElementById("historyList");
  container.innerHTML = `<p class="empty-state">読み込み中…</p>`;
  try {
    const battles = await api("/battles");
    if (!battles.length) {
      container.innerHTML = `<p class="empty-state">まだ対戦がありません</p>`;
      return;
    }
    container.innerHTML = "";
    battles.slice().reverse().forEach((b) => {
      const item = document.createElement("div");
      item.className = "history-item";
      item.innerHTML = `
        <span class="history-q">${escapeHtml(b.question)}</span>
        <span class="history-votes">A:${b.votes.a} / B:${b.votes.b} / 引:${b.votes.tie}</span>
      `;
      item.addEventListener("click", () => openHistoryBattle(b.battle_id));
      container.appendChild(item);
    });
  } catch (err) {
    container.innerHTML = `<p class="empty-state">読み込み失敗: ${escapeHtml(err.message)}</p>`;
  }
}

async function openHistoryBattle(battleId) {
  try {
    const result = await api(`/battles/${battleId}`);
    currentBattleId = battleId;
    hasVoted = false;
    document.querySelector('.tab-btn[data-view="battle"]').click();
    renderBattle({
      question: result.question,
      bot_a: result.bot_a,
      bot_b: result.bot_b,
      response_a: "(過去の回答はここには表示されません。投票結果のみ確認できます)",
      response_b: "(過去の回答はここには表示されません。投票結果のみ確認できます)",
    });
    setVoteBars({ a: result.votes_a, b: result.votes_b, tie: result.votes_tie });
  } catch (err) {
    showToast(`読み込み失敗: ${err.message}`, true);
  }
}

document.getElementById("refreshHistory").addEventListener("click", loadHistory);

// ---------- leaderboard ----------

async function loadLeaderboard() {
  const list = document.getElementById("leaderboardList");
  list.innerHTML = `<p class="empty-state">読み込み中…</p>`;
  try {
    const ranking = await api("/leaderboard");
    if (!ranking.length) {
      list.innerHTML = `<p class="empty-state">まだ対戦がありません</p>`;
      return;
    }
    list.innerHTML = "";
    ranking.forEach((entry, i) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span class="lb-rank">#${i + 1}</span>
        <span class="lb-user">${escapeHtml(entry.bot_name)}</span>
        <span class="lb-points">${entry.defeated_count} 種撃破</span>
      `;
      list.appendChild(li);
    });
  } catch (err) {
    list.innerHTML = `<p class="empty-state">読み込み失敗: ${escapeHtml(err.message)}</p>`;
  }
}

document.getElementById("refreshLeaderboard").addEventListener("click", loadLeaderboard);

// ---------- utils ----------

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}