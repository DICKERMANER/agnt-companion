const API_BASE = "http://127.0.0.1:8000";
const USER_ID = "demo_user";

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

let currentPersonaProfile = null;
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

function appendMessage(role, text, meta = "") {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = `msg ${role}`;
  bubble.textContent = text;

  row.appendChild(bubble);
  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "msg-meta";
    metaEl.textContent = meta;
    row.appendChild(metaEl);
  }

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
    currentModelLabel.textContent = "模型清單連線失敗";
    if (modelList) modelList.innerHTML = `<div class="model-error">無法讀取 /models，請確認後端 8000 有啟動。</div>`;
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
    appendSystemChip("目前連不到後端狀態，請先啟動 FastAPI 服務。");
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
    const res = await fetch(`${API_BASE}/webhook/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    appendMessage("ai", data.reply, data.model_name || data.provider);
    setState(data);
  } catch (err) {
    appendMessage("ai", "連線失敗了，稍後再試一次好嗎？", "error");
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

document.querySelectorAll(".quick-actions button").forEach((btn) => {
  btn.addEventListener("click", () => {
    sendQuickAction(btn, btn.dataset.action, btn.textContent);
  });
});

function openPersonaDrawer() {
  personaDrawer?.classList.add("open");
  personaDrawer?.setAttribute("aria-hidden", "false");
  loadPersona();
}

function closePersonaPanel() {
  personaDrawer?.classList.remove("open");
  personaDrawer?.setAttribute("aria-hidden", "true");
}

async function loadPersona() {
  try {
    const res = await fetch(`${API_BASE}/souls`);
    const data = await res.json();
    const firstSoul = data.souls[0] || {};
    currentPersonaProfile = {
      name: document.getElementById("personaName").value || firstSoul.name || "Rosé",
      birthday: document.getElementById("personaBirthday").value || firstSoul.birthday || "1997-02-11 水瓶座",
      personality: document.getElementById("personaSoul").value || firstSoul.personality || "精緻高雅、冷艷金髮女神"
    };
  } catch (err) {
    currentPersonaProfile = {
      name: "Rosé", birthday: "1997-02-11 水瓶座", personality: "精緻高雅、冷艷金髮女神"
    };
  }
}

function savePersona() {
  loadPersona(); // grabs from fields
  fetch(`${API_BASE}/persona`, { method: "POST" }).catch(() => {}); // Optional sync with backend if needed
  closePersonaPanel();
  appendSystemChip(`已載入靈魂：${currentPersonaProfile.name}`);
}

openPersonaDrawerBtn.addEventListener("click", openPersonaDrawer);
closePersonaDrawerBtn.addEventListener("click", closePersonaPanel);
personaDrawerBackdrop.addEventListener("click", closePersonaPanel);
savePersonaBtn.addEventListener("click", savePersona);

loadModels();
loadState();
