// --- 自動偵測 API 端點 ---
// 本地開發 → localhost backend；同網域裝置 → 同 IP port 8000；GitHub Pages → 引導使用本地測試
const _host = location.hostname;
const _isLoopback = _host === "127.0.0.1" || _host === "localhost" || _host === "0.0.0.0" || _host === "[::1]";

// 判斷是否為私有 IP（區網內）：10.x.x.x, 172.16-31.x.x, 192.168.x.x
const _isPrivateIP = /^(10\.\d{1,3}\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)/.test(_host);

const API_BASE = _isLoopback
  ? "http://127.0.0.1:8002"
  : _isPrivateIP
    ? `http://${_host}:8002`   // 同網域內的手機/平板自動指向同一台電腦的後端
    : (window.CYBER_COMPANION_BACKEND || "");  // GitHub Pages 需在 HTML 設定

const USER_ID = "demo_user";

// 無後端時顯示醒目提示（立即執行，不等 DOMContentLoaded）
(function showBackendWarning() {
  if (_isLoopback || _isPrivateIP || API_BASE) return;
  const banner = document.createElement("div");
  banner.id = "backend-warning";
  banner.style.cssText = "background:#ff9800;color:#000;padding:10px 16px;text-align:center;font-size:14px;font-weight:600;position:sticky;top:0;z-index:9999";
  banner.textContent = "⚠️ GitHub Pages 無法連線本地後端。請在電腦瀏覽器開啟 http://127.0.0.1:5500 測試，或用手機連同一 WiFi 開啟 http://192.168.31.13:5500";
  if (document.body) {
    document.body.prepend(banner);
  } else {
    document.addEventListener("DOMContentLoaded", () => document.body.prepend(banner), { once: true });
  }
})();

// === 軟鍵盤無縫適配 ===
(function initSoftKeyboardHandler() {
  const composer = document.querySelector(".line-composer");
  const inputField = document.getElementById("userInput");
  
  if (!inputField || !composer) return;
  
  // 監聽輸入框焦點，自動滾動到視圖內
  inputField.addEventListener("focus", () => {
    setTimeout(() => {
      // 讓輸入框及其容器完全可見
      inputField.scrollIntoView({ behavior: "smooth", block: "nearest" });
      composer.scrollIntoView({ behavior: "smooth", block: "end" });
    }, 100);
  });
  
  // iOS/Android 軟鍵盤行為差異補償
  if (/iPhone|iPad|iPod|Android/.test(navigator.userAgent)) {
    let lastInnerHeight = window.innerHeight;
    
    window.addEventListener("resize", () => {
      const currentHeight = window.innerHeight;
      if (currentHeight < lastInnerHeight) {
        // 軟鍵盤彈出，innerHeight 縮小
        inputField.scrollIntoView({ behavior: "auto", block: "nearest" });
      }
      lastInnerHeight = currentHeight;
    });
  }
})();

// === 🆕 Beta 版本信息面板初始化 ===
(function initBetaPanel() {
  if (!window.DEBUG_MODE) return;
  
  const betaPanel = document.getElementById("betaInfoPanel");
  if (!betaPanel) return;
  
  betaPanel.hidden = false;
  
  // 更新後端狀態
  const backendStatus = document.getElementById("backendStatus");
  if (API_BASE) {
    backendStatus.textContent = `✅ ${API_BASE.split("://")[0].toUpperCase()}`;
    backendStatus.style.color = "#90ee90";
  } else {
    backendStatus.textContent = "❌ 未設定";
    backendStatus.style.color = "#ff6b6b";
  }
  
  // 顯示調試模式標籤
  const debugModeLabel = document.getElementById("debugModeLabel");
  if (debugModeLabel) {
    debugModeLabel.textContent = "🧪 DEBUG ON";
    debugModeLabel.style.color = "#ffd700";
  }
  
  // 定期檢查後端連接狀態
  setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/health`, { method: "GET" });
      if (res.ok) {
        if (backendStatus) {
          backendStatus.textContent = `✅ 連接中`;
          backendStatus.style.color = "#90ee90";
        }
      }
    } catch (err) {
      if (backendStatus) {
        backendStatus.textContent = "⚠️ 連接失敗";
        backendStatus.style.color = "#ffaa44";
      }
    }
  }, 10000); // 每 10 秒檢查一次
})();

const chatWindow = document.getElementById("chatWindow");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const diamondsBalance = document.getElementById("diamondsBalance");
const favorBar = document.getElementById("favorBar");
const favorText = document.getElementById("favorText");
const stageBadge = document.getElementById("stageBadge");
const typingIndicator = document.getElementById("typingIndicator");
const fxLayer = document.getElementById("fxLayer");
const stageTransition = document.getElementById("stageTransition");
const stageTransitionText = document.getElementById("stageTransitionText");
const modelButton = document.getElementById("modelButton");
const modelDrawer = document.getElementById("modelDrawer");
const modelDrawerBackdrop = document.getElementById("modelDrawerBackdrop");
const closeModelDrawer = document.getElementById("closeModelDrawer");
const modelList = document.getElementById("modelList");
const currentModelLabel = document.getElementById("currentModelLabel");

const openPersonaDrawerBtn = document.getElementById("openPersonaDrawer");  // hidden legacy
const personaHeaderBtn    = document.getElementById("personaHeaderBtn");
const closePersonaDrawerBtn = document.getElementById("closePersonaDrawer");
const personaDrawer = document.getElementById("personaDrawer");
const personaDrawerBackdrop = document.getElementById("personaDrawerBackdrop");
const savePersonaBtn = document.getElementById("savePersona");
const soulListEl = document.getElementById("soulList");
const newSoulBtn = document.getElementById("newSoulBtn");
const importSoulBtn = document.getElementById("importSoulBtn");
const importSoulFile = document.getElementById("importSoulFile");
const exportSoulBtn = document.getElementById("exportSoulBtn");
const personaNameInput = document.getElementById("personaName");
const personaBirthdayInput = document.getElementById("personaBirthday");
const personaAvatarInput = document.getElementById("personaAvatar");
const personaSoulInput = document.getElementById("personaSoul");
const headerAvatar = document.getElementById("headerAvatar");

let currentPersonaProfile = null;
let currentSoulId = null;
let souls = [];
let pendingActionPrompt = "";
let modelRuntimeOptions = {
  thinking_enabled: false,
  fast_mode: false,
  reasoning_effort: "medium"
};

let previousStage = null;
let stageTransitionTimer = null;
let selectedModelId = null;
let models = [];
let isSending = false; // 防止重複發送

const STAGE_LABELS = {
  cold: "冷淡觀察期",
  flirty: "曖昧試探期",
  devoted: "深度依賴期",
  lover: "熱戀陪伴期",
};

function updateAvatarDisplay(avatarValue) {
  const val = avatarValue || "👑";
  if (val.startsWith("http") || val.startsWith("data:")) {
    headerAvatar.innerHTML = `<img src="${val}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
  } else {
    headerAvatar.textContent = val;
  }
}

function appendMessage(role, text, meta = "", avatarValue = null) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  if (role === "ai") {
    const avatarEl = document.createElement("div");
    avatarEl.className = "msg-avatar";
    const val = avatarValue || currentPersonaProfile?.avatar || "👑";
    if (val.startsWith("http") || val.startsWith("data:")) {
      avatarEl.innerHTML = `<img src="${val}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
    } else {
      avatarEl.textContent = val;
    }
    row.appendChild(avatarEl);
  }

  const bubbleWrapper = document.createElement("div");
  bubbleWrapper.className = "msg-bubble-wrapper";

  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;
  bubble.textContent = text;
  bubbleWrapper.appendChild(bubble);

  // 時間戳
  const now = new Date();
  const timeStr = now.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false });

  const metaEl = document.createElement("div");
  metaEl.className = "msg-meta";
  if (role === "user") {
    metaEl.innerHTML = `<span class="msg-read-status">已送出</span> ${timeStr}`;
    metaEl.dataset.readStatus = "sent";
  } else {
    metaEl.textContent = meta ? `${meta} · ${timeStr}` : timeStr;
  }
  bubbleWrapper.appendChild(metaEl);

  row.appendChild(bubbleWrapper);
  chatWindow.insertBefore(row, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return row;
}

function appendSystemChip(text) {
  const chip = document.createElement("div");
  chip.className = "system-chip compact";
  chip.textContent = text;
  chatWindow.insertBefore(chip, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTypingIndicator() {
  if (!typingIndicator) return;
  typingIndicator.hidden = false;
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function hideTypingIndicator() {
  if (!typingIndicator) return;
  typingIndicator.hidden = true;
}

function openModelDrawer() {
  modelDrawer?.classList.add("open");
  modelDrawer?.setAttribute("aria-hidden", "false");
}

function closeModelDrawerPanel() {
  modelDrawer?.classList.remove("open");
  modelDrawer?.setAttribute("aria-hidden", "true");
}

function updateCurrentModelLabel(model) {
  if (!model || !currentModelLabel) return;
  currentModelLabel.textContent = model.label || model.model || model.id;
  modelButton.textContent = model.provider === "local" ? "本地模型" : "/model";
}

function renderModels() {
  if (!modelList) return;
  modelList.innerHTML = "";

  models.forEach((model) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `model-option ${model.id === selectedModelId ? "active" : ""}`;
    button.innerHTML = `
      <span class="model-option-main">
        <strong>${model.label}</strong>
        <small>${model.provider} · ${model.model}</small>
      </span>
      <span class="model-option-badge ${model.kind}">${model.kind === "local" ? "LOCAL" : "API"}</span>
    `;
    button.addEventListener("click", () => switchModel(model.id));
    modelList.appendChild(button);
  });
}

async function loadModels() {
  try {
    const res = await fetch(`${API_BASE}/models`);
    const data = await res.json();
    models = data.models || [];
    selectedModelId = data.current_model?.id || models[0]?.id || null;
    updateCurrentModelLabel(data.current_model || models[0]);
    renderModels();
  } catch (err) {
    const hint = !API_BASE ? "（⚠️ GitHub Pages 無法連線本地後端，請用 http://127.0.0.1:5500 測試）" : "請確認後端 8002 有啟動";
    currentModelLabel.textContent = "模型清單連線失敗";
    modelButton.textContent = "⚡";
    if (modelList) modelList.innerHTML = `<div class="model-error">無法讀取 /models，${hint}。</div>`;
  }
}

async function switchModel(modelId) {
  try {
    const res = await fetch(`${API_BASE}/model`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_id: modelId }),
    });
    if (!res.ok) throw new Error("model switch failed");
    const data = await res.json();
    selectedModelId = data.current_model.id;
    updateCurrentModelLabel(data.current_model);
    renderModels();
    appendSystemChip(`已切換模型：${data.current_model.label}`);
    closeModelDrawerPanel();
  } catch (err) {
    appendSystemChip("模型切換失敗，請確認後端 /model API。");
  }
}

function triggerStageTransition(stage) {
  if (!stageTransition || !stageTransitionText) return;

  const label = STAGE_LABELS[stage] || stage;
  stageTransitionText.textContent = `${label} 已解鎖`;
  stageTransition.classList.add("show");

  window.clearTimeout(stageTransitionTimer);
  stageTransitionTimer = window.setTimeout(() => {
    stageTransition.classList.remove("show");
  }, 1800);
}

function setState(data) {
  diamondsBalance.textContent = data.diamonds_balance;
  favorBar.value = data.favorability_score;
  favorText.textContent = `${data.favorability_score} / 100`;

  if (stageBadge) {
    const stage = data.relationship_stage || "cold";
    stageBadge.textContent = STAGE_LABELS[stage] || stage;
    stageBadge.title = stage;
    stageBadge.className = `stage-badge stage-${stage}`;

    if (previousStage && previousStage !== stage) {
      triggerStageTransition(stage);
    }
    previousStage = stage;
  }
}

async function loadState() {
  try {
    const res = await fetch(`${API_BASE}/state/${USER_ID}`);
    const data = await res.json();
    setState(data);
  } catch (err) {
    const hint = !API_BASE ? "（GitHub Pages 無法連線本地後端，請改用 http://127.0.0.1:5500）" : "請先啟動 FastAPI 服務";
    appendSystemChip(`目前連不到後端狀態，${hint}。`);
  }
}

// 測試板：點擊鑽石餘額可手動輸入要設定的數量。
async function promptSetDiamonds() {
  const current = (diamondsBalance.textContent || "").trim();
  const input = window.prompt("🧪 測試板：請輸入鑽石餘額 (0~999999)", current === "--" ? "100" : current);
  if (input === null) return;
  const value = parseInt(input.trim(), 10);
  if (Number.isNaN(value) || value < 0 || value > 999999) {
    appendSystemChip("⚠️ 鑽石數量需為 0~999999 的整數");
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/state/${USER_ID}/diamonds`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diamonds_balance: value })
    });
    if (!res.ok) throw new Error("set diamonds failed");
    const data = await res.json();
    setState(data);
    appendSystemChip(`💎 已設定鑽石餘額：${data.diamonds_balance}`);
  } catch (err) {
    appendSystemChip("⚠️ 設定鑽石失敗，請確認後端服務");
  }
}

// 🆕 測試板：點擊好感度可手動調整（Beta 版測試用）
async function promptSetFavorability() {
  const current = (favorText.textContent || "").split(" / ")[0] || "0";
  const input = window.prompt("🧪 測試板：請輸入好感度 (0~100)", current);
  if (input === null) return;
  const value = parseInt(input.trim(), 10);
  if (Number.isNaN(value) || value < 0 || value > 100) {
    appendSystemChip("⚠️ 好感度需為 0~100 的整數");
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/state/${USER_ID}/favorability`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ favorability_score: value })
    });
    if (!res.ok) throw new Error("set favorability failed");
    const data = await res.json();
    setState(data);
    appendSystemChip(`💗 已設定好感度：${data.favorability_score} / 100`);
  } catch (err) {
    appendSystemChip("⚠️ 設定好感度失敗，請確認後端服務");
  }
}

function syncModelRuntimeControls() {
  modelRuntimeOptions = {
    thinking_enabled: document.getElementById("thinkingToggle")?.checked || false,
    fast_mode: document.getElementById("fastToggle")?.checked || false,
    reasoning_effort: document.getElementById("reasoningEffort")?.value || "medium"
  };
}

async function sendMessage(overridePayload = null) {
  // 防止重複發送
  if (isSending) {
    appendSystemChip("⏳ 消息發送中，請稍候...");
    return;
  }
  
  const message = overridePayload ? overridePayload.message : userInput.value.trim();
  if (!message && !overridePayload) return;

  const isQuickAction = Boolean(overridePayload && overridePayload.action_prompt);

  appendMessage("user", message, "已送出");
  userInput.value = "";
  sendBtn.disabled = true;
  isSending = true; // 標記發送中
  showTypingIndicator();

  // 抓最後一條 user 的 meta 元素，AI 回覆時更新為已讀
  const allUserMeta = chatWindow.querySelectorAll(".msg-row.user .msg-meta[data-read-status]");
  const lastUserMeta = allUserMeta[allUserMeta.length - 1];

  syncModelRuntimeControls();

  const payload = overridePayload || {
    user_id: USER_ID,
    message,
    provider: "local",
    thinking_enabled: modelRuntimeOptions.thinking_enabled,
    fast_mode: modelRuntimeOptions.fast_mode,
    reasoning_effort: modelRuntimeOptions.reasoning_effort,
    persona_profile: currentPersonaProfile || null
  };

  pendingActionPrompt = "";

  try {
    // 設定 120s timeout（本地模型推理 / 雲端 Render 冷啟動可能較慢）
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);
    
    const res = await fetch(`${API_BASE}/webhook/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(errorBody.detail ? JSON.stringify(errorBody.detail) : `HTTP ${res.status}`);
    }
    const data = await res.json();

    appendMessage("ai", data.reply, data.model_name || data.provider, data.avatar);
    // 更新最後 user 訊息為「已讀 1」
    if (lastUserMeta) {
      const timeStr = lastUserMeta.textContent.trim().replace("已送出 ", "").replace(/^已讀 1 /, "");
      lastUserMeta.innerHTML = `<span class="msg-read-status read">已讀 1</span> ${timeStr}`;
      lastUserMeta.dataset.readStatus = "read";
    }
    setState(data);
    if (isQuickAction) appendSystemChip("✅ 已送出");
  } catch (err) {
    const hint = !API_BASE ? "（⚠️ 未設定 API 端點，GitHub Pages 無法連線本地後端）" : "";
    appendMessage("ai", `連線失敗了，稍後再試一次好嗎？\n${hint}`, "error");
    if (isQuickAction) appendSystemChip("⚠️ 動作失敗，請確認後端服務後重試");
  } finally {
    hideTypingIndicator();
    sendBtn.disabled = false;
    isSending = false; // 重設發送狀態
    userInput.focus();
  }
}

function spawnParticles(sourceEl) {
  if (!fxLayer || !sourceEl) return;

  const rect = sourceEl.getBoundingClientRect();
  const originX = rect.left + rect.width / 2;
  const originY = rect.top + rect.height / 2;

  for (let i = 0; i < 12; i += 1) {
    const particle = document.createElement("span");
    particle.className = "fx-particle";
    particle.style.left = `${originX}px`;
    particle.style.top = `${originY}px`;
    particle.style.setProperty("--dx", `${(Math.random() - 0.5) * 100}px`);
    particle.style.setProperty("--dy", `${-22 - Math.random() * 70}px`);
    particle.style.animationDelay = `${Math.random() * 70}ms`;
    fxLayer.appendChild(particle);
    particle.addEventListener("animationend", () => particle.remove(), { once: true });
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});
// 輸入框有文字→顯示 send，空白→顯示 voice
userInput.addEventListener("input", () => {
  const voiceBtn = document.getElementById("voiceBtn");
  if (userInput.value.trim()) {
    sendBtn.hidden = false;
    if (voiceBtn) voiceBtn.hidden = true;
  } else {
    sendBtn.hidden = false; // keep send visible; voice is supplemental
  }
});
modelButton.addEventListener("click", openModelDrawer);
modelDrawerBackdrop.addEventListener("click", closeModelDrawerPanel);
closeModelDrawer.addEventListener("click", closeModelDrawerPanel);

function sendQuickAction(btn, action, text) {
  spawnParticles(btn);
  sendMessage({
    user_id: USER_ID,
    message: text,
    provider: "local",
    thinking_enabled: modelRuntimeOptions.thinking_enabled,
    fast_mode: modelRuntimeOptions.fast_mode,
    reasoning_effort: modelRuntimeOptions.reasoning_effort,
    persona_profile: currentPersonaProfile || null,
    action_prompt: action
  });
}

document.querySelectorAll(".line-quick-actions button").forEach((btn) => {
  btn.addEventListener("click", () => {
    sendQuickAction(btn, btn.dataset.action, btn.textContent);
  });
});

function openPersonaDrawer() {
  personaDrawer?.classList.add("open");
  personaDrawer?.setAttribute("aria-hidden", "false");
  loadSoulsList();
  loadActivePersonaIntoForm();
}

function closePersonaPanel() {
  personaDrawer?.classList.remove("open");
  personaDrawer?.setAttribute("aria-hidden", "true");
}

function fillPersonaForm({ name = "", birthday = "", soul = "", avatar = "" } = {}) {
  personaNameInput.value = name;
  personaBirthdayInput.value = birthday;
  personaAvatarInput.value = avatar;
  personaSoulInput.value = soul;
}

// Loads whatever persona is currently active for chat (the saved /persona
// override, falling back to the default soul) so re-opening the drawer
// shows the character you're actually talking to, not a blank form.
async function loadActivePersonaIntoForm() {
  try {
    const res = await fetch(`${API_BASE}/persona`);
    const data = await res.json();
    const persona = data.persona || {};
    if (persona.name) {
      fillPersonaForm({
        name: persona.name,
        birthday: persona.birthday || "",
        avatar: persona.avatar || "",
        soul: persona.soul_md || persona.personality || ""
      });
      currentPersonaProfile = persona;
      updateAvatarDisplay(persona.avatar);
      return;
    }
  } catch (err) {
    // fall through to defaults below
  }
  fillPersonaForm({ name: "Nova", birthday: "2003-09-14", avatar: "👑", soul: "" });
  updateAvatarDisplay("👑");
}

async function loadSoulsList() {
  try {
    const res = await fetch(`${API_BASE}/souls`);
    if (!res.ok) throw new Error("souls list failed");
    const data = await res.json();
    souls = data.souls || [];
    renderSoulList();
  } catch (err) {
    if (soulListEl) soulListEl.innerHTML = `<div class="model-error">無法讀取角色清單，請確認後端服務。</div>`;
  }
}

function renderSoulList() {
  if (!soulListEl) return;
  soulListEl.innerHTML = "";
  souls.forEach((soul) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `soul-chip ${soul.id === currentSoulId ? "active" : ""}`;
    chip.textContent = soul.name || soul.id;
    chip.addEventListener("click", () => selectSoul(soul.id));
    soulListEl.appendChild(chip);
  });
}

async function selectSoul(soulId) {
  try {
    const res = await fetch(`${API_BASE}/souls/${encodeURIComponent(soulId)}`);
    if (!res.ok) throw new Error("soul not found");
    const soul = await res.json();
    currentSoulId = soulId;
    fillPersonaForm({
      name: soul.name,
      birthday: soul.birthday || "",
      avatar: soul.avatar || "👑",
      soul: soul.system_prompt_base || ""
    });
    // 立即更新頭貼預覽與 header
    if (soul.avatar) personaAvatarInput.value = soul.avatar;
    updateAvatarDisplay(soul.avatar || "👑");
    renderSoulList();
  } catch (err) {
    appendSystemChip("⚠️ 載入角色失敗，請稍後再試");
  }
}

function startNewSoul() {
  currentSoulId = null;
  fillPersonaForm({ name: "", birthday: "", avatar: "👑", soul: "" });
  renderSoulList();
}

async function savePersona() {
  const name = personaNameInput.value.trim();
  const birthday = personaBirthdayInput.value.trim();
  const avatar = personaAvatarInput.value.trim();
  const soulText = personaSoulInput.value.trim();

  if (!name) {
    appendSystemChip("⚠️ 請先輸入角色名稱再儲存");
    return;
  }

  savePersonaBtn.disabled = true;
  try {
    // Persist as a reusable soul in the harem library.
    const soulRes = await fetch(`${API_BASE}/souls`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: currentSoulId || undefined,
        name,
        birthday,
        personality: soulText,
        system_prompt_base: soulText,
        avatar: avatar || "👑"
      })
    });
    if (!soulRes.ok) throw new Error("souls save failed");
    const soulData = await soulRes.json();
    currentSoulId = soulData.soul.id;

    // Persist as the active override used by every /webhook/chat call.
    const personaRes = await fetch(`${API_BASE}/persona`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, birthday, avatar: avatar || "👑", personality: soulText, soul_md: soulText })
    });
    if (!personaRes.ok) throw new Error("persona save failed");
    const personaData = await personaRes.json();
    currentPersonaProfile = personaData.persona;
    updateAvatarDisplay(currentPersonaProfile.avatar);

    await loadSoulsList();
    appendSystemChip(`💗 已儲存靈魂：${name}`);
    closePersonaPanel();
  } catch (err) {
    appendSystemChip("⚠️ 儲存靈魂失敗，請確認後端服務後重試");
  } finally {
    savePersonaBtn.disabled = false;
  }
}

function exportSoul() {
  const name = personaNameInput.value.trim() || "未命名角色";
  const birthday = personaBirthdayInput.value.trim();
  const soulText = personaSoulInput.value.trim();

  const markdown = `---\nname: "${name}"\nbirthday: "${birthday}"\nzodiac: ""\npersonality: ""\n---\n${soulText}\n`;
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${currentSoulId || "soul"}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function importSoulFromFile(file) {
  const text = await file.text();
  const idGuess = file.name.replace(/\.md$/i, "") || `imported-${Date.now()}`;
  try {
    const res = await fetch(`${API_BASE}/souls/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: idGuess, markdown: text })
    });
    if (!res.ok) throw new Error("import failed");
    const data = await res.json();
    currentSoulId = data.soul.id;
    await loadSoulsList();
    await selectSoul(currentSoulId);
    appendSystemChip(`📥 已匯入靈魂：${data.soul.name}`);
  } catch (err) {
    appendSystemChip("⚠️ 匯入 Soul.md 失敗，請確認檔案格式");
  }
}

openPersonaDrawerBtn?.addEventListener("click", openPersonaDrawer);
personaHeaderBtn?.addEventListener("click", openPersonaDrawer);
closePersonaDrawerBtn.addEventListener("click", closePersonaPanel);
personaDrawerBackdrop.addEventListener("click", closePersonaPanel);
savePersonaBtn.addEventListener("click", savePersona);
newSoulBtn?.addEventListener("click", startNewSoul);
exportSoulBtn?.addEventListener("click", exportSoul);
importSoulBtn?.addEventListener("click", () => importSoulFile?.click());
importSoulFile?.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) importSoulFromFile(file);
  e.target.value = "";
});

// --- Avatar upload wiring (was completely missing) ---
const uploadAvatarBtn = document.getElementById("uploadAvatarBtn");
const avatarUploadFile = document.getElementById("avatarUploadFile");
const avatarPreview = document.getElementById("avatarPreview");

uploadAvatarBtn?.addEventListener("click", () => avatarUploadFile?.click());
avatarUploadFile?.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const dataUrl = reader.result;
    personaAvatarInput.value = dataUrl;
    if (avatarPreview) {
      if (typeof dataUrl === "string" && dataUrl.startsWith("data:image")) {
        avatarPreview.innerHTML = `<img src="${dataUrl}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" />`;
      } else {
        avatarPreview.textContent = "👑";
      }
    }
    updateAvatarDisplay(dataUrl);
    appendSystemChip("📷 頭貼已上傳（儲存靈魂後生效）");
  };
  reader.readAsDataURL(file);
  e.target.value = "";
});

const avatarAiPromptBtn = document.getElementById("avatarAiPromptBtn");
avatarAiPromptBtn?.addEventListener("click", () => {
  closePersonaPanel();
  sendQuickAction(avatarAiPromptBtn, avatarAiPromptBtn.dataset.action, avatarAiPromptBtn.textContent);
});

loadModels();
loadState();

// 初始化時預載角色頭貼（從 /persona 或預設 soul）
(async function preloadAvatar() {
  try {
    const personaRes = await fetch(`${API_BASE}/persona`);
    const personaData = await personaRes.json();
    const persona = personaData.persona || {};
    if (persona.avatar) {
      updateAvatarDisplay(persona.avatar);
      personaAvatarInput.value = persona.avatar;
      return;
    }
  } catch (_) {}
  // fallback: 從第一個 soul 載入頭貼
  try {
    const soulsRes = await fetch(`${API_BASE}/souls`);
    const soulsData = await soulsRes.json();
    const souls = soulsData.souls || [];
    if (souls[0]) {
      updateAvatarDisplay(souls[0].avatar || "👑");
    }
  } catch (_) {}
})();

// 測試板：點鑽石餘額可手動設定數量。
if (diamondsBalance?.parentElement) {
  diamondsBalance.parentElement.addEventListener("click", promptSetDiamonds);
  diamondsBalance.parentElement.style.cursor = "pointer";
  diamondsBalance.parentElement.title = window.DEBUG_MODE ? "🧪 點我設定鑽石（測試板）" : "💎 鑽石餘額";
}

// 🆕 好感度也可點擊調整（Beta 測試用）
if (favorText) {
  // 只在 DEBUG_MODE 下才顯示可點擊的提示
  if (window.DEBUG_MODE) {
    favorText.addEventListener("click", promptSetFavorability);
    favorText.style.cursor = "pointer";
    favorText.title = "🧪 點我設定好感度（測試板）";
  } else {
    favorText.style.cursor = "default";
  }
}

// ============================================================
// 📎 媒體選單 — 拍照 / 相冊 / 文件 / 錄音
// ============================================================
(function initMediaFeatures() {
  const mediaMenuBtn = document.getElementById("mediaMenuBtn");
  const mediaMenu    = document.getElementById("mediaMenu");
  const mmCamera     = document.getElementById("mmCamera");
  const mmPhoto      = document.getElementById("mmPhoto");
  const mmFile       = document.getElementById("mmFile");
  const mmVoice      = document.getElementById("mmVoice");
  const cameraInput  = document.getElementById("cameraInput");
  const photoInput   = document.getElementById("photoInput");
  const fileInput    = document.getElementById("fileInput");

  // toggle 媒體選單
  mediaMenuBtn?.addEventListener("click", () => {
    const open = !mediaMenu.hidden;
    mediaMenu.hidden = open;
    if (!open) { stickerPanel.hidden = true; }  // 關貼圖
  });

  // 拍照
  mmCamera?.addEventListener("click", () => { mediaMenu.hidden = true; cameraInput?.click(); });
  // 相冊
  mmPhoto?.addEventListener("click",  () => { mediaMenu.hidden = true; photoInput?.click();  });
  // 文件
  mmFile?.addEventListener("click",   () => { mediaMenu.hidden = true; fileInput?.click();   });
  // 錄音入口
  mmVoice?.addEventListener("click",  () => { mediaMenu.hidden = true; startVoiceRecording(); });

  // 處理圖片選擇（拍照 / 相冊）
  function handleImageFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      appendImageBubble("user", reader.result, file.name);
      // 傳給 AI：描述圖片 (純前端；可擴充為 multipart POST)
      sendMessage({
        user_id: USER_ID,
        message: `（傳送了一張圖片：${file.name}）`,
        provider: "local",
        thinking_enabled: modelRuntimeOptions.thinking_enabled,
        fast_mode: modelRuntimeOptions.fast_mode,
        reasoning_effort: modelRuntimeOptions.reasoning_effort,
        persona_profile: currentPersonaProfile || null,
        action_prompt: "使用者傳來了一張圖片，請用角色口吻自然回應這件事。"
      });
    };
    reader.readAsDataURL(file);
  }
  cameraInput?.addEventListener("change", e => { handleImageFile(e.target.files?.[0]); e.target.value = ""; });
  photoInput?.addEventListener("change",  e => { handleImageFile(e.target.files?.[0]); e.target.value = ""; });

  // 處理文件選擇
  fileInput?.addEventListener("change", e => {
    const file = e.target.files?.[0];
    if (!file) return;
    appendDocBubble("user", file.name, file.size);
    sendMessage({
      user_id: USER_ID,
      message: `（傳送了一個文件：${file.name}，${(file.size/1024).toFixed(1)} KB）`,
      provider: "local",
      thinking_enabled: modelRuntimeOptions.thinking_enabled,
      fast_mode: modelRuntimeOptions.fast_mode,
      reasoning_effort: modelRuntimeOptions.reasoning_effort,
      persona_profile: currentPersonaProfile || null,
      action_prompt: "使用者傳來了一個文件，請用角色口吻自然回應這件事。"
    });
    e.target.value = "";
  });
  // 點擊其他地方關閉媒體選單
  document.addEventListener("click", e => {
    if (!mediaMenuBtn?.contains(e.target) && !mediaMenu?.contains(e.target)) {
      if (mediaMenu) mediaMenu.hidden = true;
    }
  });
})();

// ============================================================
// 📨 圖片 / 文件氣泡
// ============================================================
function appendImageBubble(role, src, filename) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  const wrapper = document.createElement("div");
  wrapper.className = "msg-bubble-wrapper";
  const bubble = document.createElement("div");
  bubble.className = `msg ${role} msg-image`;
  
  // 安全地創建圖片元素，避免屬性注入
  const img = document.createElement("img");
  img.src = src;
  img.alt = filename; // setAttribute 會自動轉義，textContent 也安全
  img.style.cssText = "max-width:200px;max-height:200px;border-radius:12px;display:block;cursor:pointer;";
  img.addEventListener("click", () => {
    if (img.requestFullscreen) {
      img.requestFullscreen().catch(() => {});
    }
  });
  
  bubble.appendChild(img);
  wrapper.appendChild(bubble);
  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.textContent = "已送出";
  wrapper.appendChild(meta);
  row.appendChild(wrapper);
  chatWindow.insertBefore(row, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendDocBubble(role, filename, size) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  const wrapper = document.createElement("div");
  wrapper.className = "msg-bubble-wrapper";
  const bubble = document.createElement("div");
  bubble.className = `msg ${role} msg-doc`;
  
  // 安全地組合文件氣泡，避免 XSS
  const icon = document.createElement("span");
  icon.className = "doc-icon";
  icon.textContent = "📄";
  
  const nameSpan = document.createElement("span");
  nameSpan.className = "doc-name";
  nameSpan.textContent = filename; // 用 textContent 避免 HTML 注入
  
  const sizeSpan = document.createElement("span");
  sizeSpan.className = "doc-size";
  sizeSpan.textContent = `${(size/1024).toFixed(1)} KB`;
  
  bubble.appendChild(icon);
  bubble.appendChild(nameSpan);
  bubble.appendChild(sizeSpan);
  
  wrapper.appendChild(bubble);
  const meta = document.createElement("div");
  meta.className = "msg-meta";
  meta.textContent = "已送出";
  wrapper.appendChild(meta);
  row.appendChild(wrapper);
  chatWindow.insertBefore(row, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

// ============================================================
// 😊 貼圖面板
// ============================================================
(function initStickerPanel() {
  const stickerBtn = document.getElementById("stickerBtn");
  const stickerPanel = document.getElementById("stickerPanel");
  const stickerGrid  = document.getElementById("stickerGrid");

  // 貼圖庫（可擴充）
  const STICKERS = [
    "😍","🥰","😘","💕","💋","🤗","😏","🫦",
    "🥺","😭","😤","🙄","😂","🤣","😎","🥳",
    "👋","🫶","💪","🙏","👍","✌️","🤞","💯",
    "🌹","🍑","🍒","🍭","🍫","🎀","🎉","🔥",
    "💎","👑","⭐","🌙","🌸","🦋","🐱","🐰",
  ];

  if (stickerGrid) {
    STICKERS.forEach(emoji => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "sticker-item";
      btn.textContent = emoji;
      btn.addEventListener("click", () => {
        if (stickerPanel) stickerPanel.hidden = true;
        sendMessage({
          user_id: USER_ID,
          message: emoji,
          provider: "local",
          thinking_enabled: modelRuntimeOptions.thinking_enabled,
          fast_mode: modelRuntimeOptions.fast_mode,
          reasoning_effort: modelRuntimeOptions.reasoning_effort,
          persona_profile: currentPersonaProfile || null,
          action_prompt: `使用者傳了貼圖「${emoji}」，請用角色口吻自然回應這個表情。`
        });
      });
      stickerGrid.appendChild(btn);
    });
  }

  stickerBtn?.addEventListener("click", e => {
    e.stopPropagation();
    if (stickerPanel) {
      stickerPanel.hidden = !stickerPanel.hidden;
      document.getElementById("mediaMenu").hidden = true;
    }
  });

  document.addEventListener("click", e => {
    if (!stickerBtn?.contains(e.target) && !stickerPanel?.contains(e.target)) {
      if (stickerPanel) stickerPanel.hidden = true;
    }
  });
})();

// ============================================================
// 🎙️ 錄音功能 (Web Audio API)
// ============================================================
let _mediaRecorder = null;
let _audioChunks   = [];
let _recordingTimer = null;

function startVoiceRecording() {
  if (_mediaRecorder && _mediaRecorder.state === "recording") return;
  navigator.mediaDevices?.getUserMedia({ audio: true }).then(stream => {
    _audioChunks = [];
    _mediaRecorder = new MediaRecorder(stream);
    _mediaRecorder.ondataavailable = e => { if (e.data.size > 0) _audioChunks.push(e.data); };
    _mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(_audioChunks, { type: "audio/webm" });
      appendAudioBubble("user", blob);
      appendSystemChip("🎙️ 語音訊息已傳送（AI 以文字回覆）");
      sendMessage({
        user_id: USER_ID,
        message: "（傳送了一段語音訊息）",
        provider: "local",
        thinking_enabled: modelRuntimeOptions.thinking_enabled,
        fast_mode: modelRuntimeOptions.fast_mode,
        reasoning_effort: modelRuntimeOptions.reasoning_effort,
        persona_profile: currentPersonaProfile || null,
        action_prompt: "使用者傳來了語音訊息，請用角色口吻溫柔回應。"
      });
    };
    _mediaRecorder.start();
    appendSystemChip("🔴 錄音中… 點選下方停止鍵結束");
    showRecordingUI();
  }).catch(() => {
    appendSystemChip("⚠️ 麥克風授權失敗，請允許瀏覽器使用麥克風");
  });
}

function stopVoiceRecording() {
  if (_mediaRecorder && _mediaRecorder.state === "recording") {
    _mediaRecorder.stop();
    hideRecordingUI();
  }
}

function showRecordingUI() {
  const voiceBtn = document.getElementById("voiceBtn");
  const sendBtn  = document.getElementById("sendBtn");
  if (voiceBtn) { voiceBtn.hidden = false; voiceBtn.textContent = "⏹ 停止"; voiceBtn.classList.add("recording"); }
  if (sendBtn)  sendBtn.hidden = true;
  clearInterval(_recordingTimer);
  let sec = 0;
  _recordingTimer = setInterval(() => {
    sec++;
    if (voiceBtn) voiceBtn.textContent = `⏹ ${sec}s`;
    if (sec >= 60) stopVoiceRecording();  // 最長 60s
  }, 1000);
}

function hideRecordingUI() {
  const voiceBtn = document.getElementById("voiceBtn");
  const sendBtn  = document.getElementById("sendBtn");
  if (voiceBtn) { voiceBtn.hidden = true; voiceBtn.classList.remove("recording"); }
  if (sendBtn)  sendBtn.hidden = false;
  clearInterval(_recordingTimer);
}

document.getElementById("voiceBtn")?.addEventListener("click", stopVoiceRecording);

function appendAudioBubble(role, blob) {
  const url = URL.createObjectURL(blob);
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;
  const wrapper = document.createElement("div");
  wrapper.className = "msg-bubble-wrapper";
  const bubble = document.createElement("div");
  bubble.className = `msg ${role} msg-audio`;
  bubble.innerHTML = `🎙️ <audio controls src="${url}" style="max-width:180px;vertical-align:middle;"></audio>`;
  wrapper.appendChild(bubble);
  row.appendChild(wrapper);
  chatWindow.insertBefore(row, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}
