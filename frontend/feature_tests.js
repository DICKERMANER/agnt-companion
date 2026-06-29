const fs = require('fs');
const path = require('path');

const root = __dirname;
const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const css = fs.readFileSync(path.join(root, 'styles.css'), 'utf8');

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function getFunctionBody(source, functionName) {
  const start = source.indexOf(`function ${functionName}`);
  assert(start >= 0, `${functionName} should exist`);
  const nextFunction = source.indexOf('\nfunction ', start + 1);
  return source.slice(start, nextFunction === -1 ? source.length : nextFunction);
}

function testTypingIndicatorMarkupAndLogic() {
  assert(index.includes('id="typingIndicator"'), 'index.html should contain #typingIndicator for AI typing state');
  assert(css.includes('.typing-indicator'), 'styles.css should style .typing-indicator');
  assert(app.includes('showTypingIndicator'), 'app.js should expose showTypingIndicator logic');
  assert(app.includes('hideTypingIndicator'), 'app.js should expose hideTypingIndicator logic');

  const sendMessageBody = getFunctionBody(app, 'sendMessage');
  assert(sendMessageBody.indexOf('showTypingIndicator()') < sendMessageBody.indexOf('fetch(`${API_BASE}/webhook/chat`'), 'typing indicator should show before chat fetch');
  assert(sendMessageBody.includes('finally'), 'sendMessage should clean up loading state in finally');
  assert(sendMessageBody.indexOf('hideTypingIndicator()') > sendMessageBody.indexOf('fetch(`${API_BASE}/webhook/chat`'), 'typing indicator should hide after chat fetch path is entered');
}

function testQuickActionParticles() {
  assert(index.includes('id="fxLayer"'), 'index.html should contain #fxLayer for visual effects');
  assert(css.includes('.fx-particle'), 'styles.css should style .fx-particle');
  assert(app.includes('spawnParticles'), 'app.js should implement spawnParticles');
  assert(app.includes('.line-quick-actions button'), 'quick action click handler should target the canonical .line-quick-actions selector');
  assert(app.includes('btn.addEventListener("click"'), 'quick action click handler should exist');
  assert(app.includes('spawnParticles(btn'), 'quick action click should spawn particles from clicked button');
  assert(app.includes('sendQuickAction'), 'quick action buttons should trigger an actual chat action');
  assert(app.includes('sendMessage({'), 'quick actions should call sendMessage with an override payload');
}

function testPersonaHaremUi() {
  assert(index.includes('id="personaDrawer"'), 'index.html should include persona drawer');
  assert(index.includes('id="openPersonaDrawer"'), 'plus button should open persona drawer');
  assert(index.includes('id="personaName"'), 'persona form should include name field');
  assert(index.includes('id="personaBirthday"'), 'persona form should include birthday field');
  assert(index.includes('id="personaSoul"'), 'persona form should include Soul.md field');
  assert(index.includes('id="savePersona"'), 'persona form should include save button');
  assert(css.includes('.persona-panel'), 'styles.css should style persona panel');
  assert(css.includes('.persona-form'), 'styles.css should style persona form');
  assert(app.includes('loadActivePersonaIntoForm'), 'app.js should load the active persona profile into the form');
  assert(app.includes('async function savePersona'), 'app.js should save persona profile');
  assert(app.includes('/persona'), 'app.js should call persona endpoint');
  assert(app.includes('persona_profile'), 'chat payload should include persona_profile');

  const savePersonaBody = getFunctionBody(app, 'savePersona');
  assert(savePersonaBody.includes('method: "POST"') && savePersonaBody.includes('body: JSON.stringify'),
    'savePersona should POST an actual JSON body, not an empty request');
}

function testSoulHaremManagement() {
  assert(index.includes('id="soulList"'), 'index.html should include a soul harem list container');
  assert(index.includes('id="newSoulBtn"'), 'index.html should include a button to start a new soul');
  assert(index.includes('id="importSoulBtn"'), 'index.html should include a Soul.md import button');
  assert(index.includes('id="exportSoulBtn"'), 'index.html should include a Soul.md export button');
  assert(index.includes('id="importSoulFile"'), 'index.html should include a hidden file input for import');
  assert(css.includes('.soul-list'), 'styles.css should style the soul harem list');
  assert(css.includes('.soul-chip'), 'styles.css should style individual soul chips');
  assert(app.includes('async function loadSoulsList'), 'app.js should fetch the saved souls list');
  assert(app.includes('async function selectSoul'), 'app.js should support selecting a saved soul');
  assert(app.includes('/souls'), 'app.js should call the /souls endpoint');
  assert(app.includes('/souls/import'), 'app.js should call the /souls/import endpoint');
  assert(app.includes('async function exportSoul') || app.includes('function exportSoul'),
    'app.js should support exporting the current soul as Soul.md');
}

function testFavorStageTransition() {
  assert(index.includes('id="stageTransition"'), 'index.html should contain #stageTransition overlay');
  assert(css.includes('.stage-transition'), 'styles.css should style .stage-transition');
  assert(app.includes('previousStage'), 'app.js should track previousStage');
  assert(app.includes('triggerStageTransition'), 'app.js should implement triggerStageTransition');
  assert(app.includes('stageTransition'), 'app.js should reference the transition overlay');
}

function testLineStyleShell() {
  assert(index.includes('line-app-shell'), 'index.html should use LINE-like app shell');
  assert(index.includes('line-chat-header'), 'index.html should use LINE-like chat header');
  assert(index.includes('line-composer'), 'index.html should use LINE-like composer');
  assert(css.includes('--line-green'), 'styles.css should define LINE green token');
  assert(css.includes('.msg.user::after'), 'styles.css should add user bubble tail');
  assert(css.includes('.msg.ai::before'), 'styles.css should add ai bubble tail');
}

function testModelSwitcherUi() {
  assert(index.includes('id="modelButton"'), 'index.html should include model switch button');
  assert(index.includes('id="modelDrawer"'), 'index.html should include model drawer');
  assert(index.includes('id="modelList"'), 'index.html should include model list container');
  assert(app.includes('loadModels'), 'app.js should load models from backend');
  assert(app.includes('/models'), 'app.js should call /models endpoint');
  assert(app.includes('/model'), 'app.js should call /model endpoint to switch');
  assert(app.includes('selectedModelId'), 'app.js should track selected model');
}

function testModelRuntimeControls() {
  assert(index.includes('id="thinkingToggle"'), 'index.html should include thinking toggle');
  assert(index.includes('id="fastToggle"'), 'index.html should include fast toggle');
  assert(index.includes('id="reasoningEffort"'), 'index.html should include reasoning effort select');
  assert(index.includes('value="minimal"'), 'reasoning effort should include minimal');
  assert(index.includes('value="low"'), 'reasoning effort should include low');
  assert(index.includes('value="medium"'), 'reasoning effort should include medium');
  assert(index.includes('value="high"'), 'reasoning effort should include high');
  assert(index.includes('value="max"'), 'reasoning effort should include max');
  assert(css.includes('.model-settings-card'), 'styles.css should style model settings card');
  assert(css.includes('.switch-input'), 'styles.css should style toggle switch input');
  assert(app.includes('modelRuntimeOptions'), 'app.js should track model runtime options');
  assert(app.includes('syncModelRuntimeControls'), 'app.js should sync runtime controls');
  assert(app.includes('reasoning_effort'), 'chat payload should include reasoning_effort');
  assert(app.includes('thinking_enabled'), 'chat payload should include thinking_enabled');
  assert(app.includes('fast_mode'), 'chat payload should include fast_mode');
}

const tests = [
  testTypingIndicatorMarkupAndLogic,
  testQuickActionParticles,
  testPersonaHaremUi,
  testSoulHaremManagement,
  testFavorStageTransition,
  testLineStyleShell,
  testModelSwitcherUi,
  testModelRuntimeControls,
];

for (const test of tests) {
  test();
  console.log(`PASS ${test.name}`);
}

console.log(`All ${tests.length} frontend feature tests passed.`);
