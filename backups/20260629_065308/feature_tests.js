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
  assert(app.includes('btn.addEventListener("click"'), 'quick action click handler should exist');
  assert(app.includes('spawnParticles(btn'), 'quick action click should spawn particles from clicked button');
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

const tests = [
  testTypingIndicatorMarkupAndLogic,
  testQuickActionParticles,
  testFavorStageTransition,
  testLineStyleShell,
  testModelSwitcherUi,
];

for (const test of tests) {
  test();
  console.log(`PASS ${test.name}`);
}

console.log(`All ${tests.length} frontend feature tests passed.`);
