// --- 自動偵測 API 端點 ---
// 本地開發 → localhost backend；同網域裝置 → 同 IP port 8000；GitHub Pages → 引導使用本地測試
const _host = location.hostname;
const _isLoopback = _host === "127.0.0.1" || _host === "localhost" || _host === "0.0.0.0" || _host === "[::1]";

// 判斷是否為私有 IP（區網內）：10.x.x.x, 172.16-31.x.x, 192.168.x.x
const _isPrivateIP = /^(10\.\d{1,3}\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.)/.test(_host);

const API_BASE = _isLoopback
  ? "http://127.0.0.1:8000"
  : _isPrivateIP
    ? `http://${_host}:8000`   // 同網域內的手機/平板自動指向同一台電腦的後端
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

const openPersonaDrawerBtn = document.getElementById("openPersonaDrawer");
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

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "msg-meta";
    metaEl.textContent = meta;
    bubbleWrapper.appendChild(metaEl);
  }

  row.appendChild(bubbleWrapper);
  chatWindow.insertBefore(row, typingIndicator || null);
  chatWindow.scrollTop = chatWindow.scrollHeight;
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
    const hint = !API_BASE ? "（⚠️ GitHub Pages 無法連線本地後端，請用 http://127.0.0.1:5500 測試）" : "請確認後端 8000 有啟動";
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
  const input = window.prompt("測試板：請輸入鑽石餘額 (0~999999)", current === "--" ? "100" : current);
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

function syncModelRuntimeControls() {
  modelRuntimeOptions = {
    thinking_enabled: document.getElementById("thinkingToggle")?.checked || false,
    fast_mode: document.getElementById("fastToggle")?.checked || false,
    reasoning_effort: document.getElementById("reasoningEffort")?.value || "medium"
  };
}

async function sendMessage(overridePayload = null) {
  const message = overridePayload ? overridePayload.message : userInput.value.trim();
  if (!message && !overridePayload) return;

  const isQuickAction = Boolean(overridePayload && overridePayload.action_prompt);

  appendMessage("user", message, "已送出");
  userInput.value = "";
  sendBtn.disabled = true;
  showTypingIndicator();

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
    // 設定 120s timeout（本地模型推理 + tunnel 延遲）
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
    setState(data);
    if (isQuickAction) appendSystemChip("✅ 已送出");
  } catch (err) {
    const hint = !API_BASE ? "（⚠️ 未設定 API 端點，GitHub Pages 無法連線本地後端）" : "";
    appendMessage("ai", `連線失敗了，稍後再試一次好嗎？\n${hint}`, "error");
    if (isQuickAction) appendSystemChip("⚠️ 動作失敗，請確認後端服務後重試");
  } finally {
    hideTypingIndicator();
    sendBtn.disabled = false;
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

openPersonaDrawerBtn.addEventListener("click", openPersonaDrawer);
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
  diamondsBalance.parentElement.title = "點我設定鑽石（測試板）";
}
