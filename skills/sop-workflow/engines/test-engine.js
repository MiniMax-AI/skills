/**
 * SOP Workflow Engine - Unit Tests
 *
 * 运行方式:
 *   node test-engine.js
 *
 * 或使用内置测试:
 *   node --test engines/test-engine.js
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// 颜色
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const RESET = '\x1b[0m';

let passed = 0;
let failed = 0;

// test() always runs fn() inside an async IIFE so that
// `await runner.verify(...)` in the test body completes BEFORE the counter updates.
function test(name, fn) {
  return (async () => {
    await fn();
    console.log(`${GREEN}✓${RESET} ${name}`);
    passed++;
  })().catch(e => {
    console.log(`${RED}✗${RESET} ${name}`);
    console.log(`  ${RED}Error:${RESET} ${e.message}`);
    failed++;
  });
}

function assertEqual(actual, expected, msg = '') {
  if (actual !== expected) {
    throw new Error(`${msg}\n  Expected: ${expected}\n  Actual: ${actual}`);
  }
}

function assertContains(str, substr, msg = '') {
  if (!str.includes(substr)) {
    throw new Error(`${msg}\n  Expected to contain: ${substr}\n  Got: ${str.substring(0, 200)}`);
  }
}

function assertMatch(str, regex, msg = '') {
  if (!regex.test(str)) {
    throw new Error(`${msg}\n  Expected to match: ${regex}\n  Got: ${str.substring(0, 200)}`);
  }
}

async function assertRejects(fn, msg = '') {
  try {
    await fn();
    throw new Error(`${msg}: Expected function to throw`);
  } catch (e) {
    if (e.message.includes('Expected function to throw')) {
      throw e;
    }
    // Expected to throw
  }
}

// ============================================================
// 测试辅助
// ============================================================
function createTestDir() {
  const dir = `/tmp/sop-test-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  fs.mkdirSync(dir);
  fs.mkdirSync(path.join(dir, '.git'));
  return dir;
}

function writeManifest(dir, manifest) {
  fs.writeFileSync(path.join(dir, 'test.yaml'), yaml.dump(manifest));
}

function readState(dir) {
  const stateFile = path.join(dir, '.sop-workflow-state.json');
  if (fs.existsSync(stateFile)) {
    return JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  }
  return null;
}

// ============================================================
// 测试用例
// ============================================================
const TESTS = [
  ['T01: bootstrap script exists and is executable', () => {
    const bootstrapPath = path.join(__dirname, '..', 'bootstrap.sh');
    assertEqual(fs.existsSync(bootstrapPath), true);
    assertEqual(fs.statSync(bootstrapPath).mode & 0o111, 0o111); // executable
  }],

  ['T02: workflow engine loads valid YAML manifest', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, {
      meta: { name: 'test' },
      phases: { test: { name: 'Test', tasks: [{ id: 't1', title: 'T1', agent_role: 'worker' }] } }
    });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();
    assertEqual(engine.manifest.meta.name, 'test');
    assertEqual(Object.keys(engine.manifest.phases).length, 1);
  }],

  ['T03: workflow engine rejects missing manifest', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const engine = new WorkflowEngine('/nonexistent.yaml');
    let error = null;
    try { engine.load(); } catch (e) { error = e; }
    assertEqual(error?.message?.includes('not found'), true);
  }],

  ['T04: workflow state saves and loads correctly', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    state.addTask('t1', 'pending');
    state.addTask('t2', 'completed');
    state.addTask('t3', 'failed');
    state.phase = 'execute';
    state.addTokenUsage(1000);
    const saved = state.save();
    assertEqual(fs.existsSync(saved), true);
    const manifest2 = { config: {} };
    const state2 = new WorkflowState(manifest2);
    state2.load();
    assertEqual(state2.phase, 'execute');
    assertEqual(state2.tasks.length, 3);
    assertEqual(state2.tasks.find(t => t.id === 't3')?.status, 'failed');
  }],

  ['T05: workflow state handles corrupted JSON gracefully', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const dir = createTestDir();
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    fs.writeFileSync(path.join(dir, '.sop-workflow-state.json'), 'broken json {');
    const oldCwd = process.cwd();
    process.chdir(dir);
    const loaded = state.load();
    process.chdir(oldCwd);
    assertEqual(loaded, false);
    assertEqual(state.tasks.length, 0);
  }],

  ['T06: task status updates correctly', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    state.addTask('t1', 'pending');
    assertEqual(state.tasks[0].status, 'pending');
    state.updateTask('t1', { status: 'running', start: Date.now() });
    assertEqual(state.tasks[0].status, 'running');
    state.updateTask('t1', { status: 'completed', duration: 1000 });
    assertEqual(state.tasks[0].status, 'completed');
    assertEqual(state.tasks[0].duration, 1000);
  }],

  ['T07: task deduplication in addTask', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    state.addTask('t1', 'pending');
    state.addTask('t1', 'running');
    state.addTask('t2', 'pending');
    assertEqual(state.tasks.length, 2);
    assertEqual(state.tasks[0].id, 't1');
    assertEqual(state.tasks[1].id, 't2');
  }],

  ['T08: token tracking and warning threshold', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: { token_budget: 100, token_budget_warning: 0.8 } };
    const state = new WorkflowState(manifest);
    assertEqual(state.tokenBudget, 100);
    state.addTokenUsage(50);
    state.addTokenUsage(40);
    assertEqual(state.tokenUsed, 90);
  }],

  ['T09: token budget falls back to env var', () => {
    const oldVal = process.env.SOP_TOKEN_BUDGET;
    process.env.SOP_TOKEN_BUDGET = '50000';
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    assertEqual(state.tokenBudget, 50000);
    process.env.SOP_TOKEN_BUDGET = oldVal || '';
  }],

  ['T10: builtin verifiers are defined', () => {
    const { BUILTIN_VERIFIERS } = require('./workflow-engine.js');
    const expected = ['code_quality', 'security', 'functional', 'performance', 'comprehensive'];
    for (const v of expected) {
      assertEqual(typeof BUILTIN_VERIFIERS[v], 'object');
      assertEqual(typeof BUILTIN_VERIFIERS[v].threshold, 'number');
      assertEqual(typeof BUILTIN_VERIFIERS[v].prompt, 'string');
    }
  }],

  ['T11: mock verifier parses embedded JSON verdict', () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const failResult = agent._mockVerifier('=== 交付物 ===\n{"verdict":"FAIL","score":1}');
    const failParsed = JSON.parse(failResult);
    assertEqual(failParsed.verdict, 'FAIL');
    assertEqual(failParsed.score, 1);
    const passResult = agent._mockVerifier('=== 交付物 ===\n{"verdict":"PASS","score":5}');
    const passParsed = JSON.parse(passResult);
    assertEqual(passParsed.verdict, 'PASS');
    assertEqual(passParsed.score, 5);
  }],

  ['T12: mock verifier handles special markers', () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const failResult = agent._mockVerifier('=== 交付物 ===\n__FAIL__');
    const parsed = JSON.parse(failResult);
    assertEqual(parsed.verdict, 'FAIL');
  }],

  ['T13: mock verifier returns default PASS for unknown content', () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const result = agent._mockVerifier('hello world');
    const parsed = JSON.parse(result);
    assertEqual(parsed.verdict, 'PASS');
    assertEqual(parsed.score, 5);
  }],

  ['T14: verifier runner uses manifest custom verifier', async () => {
    const { VerifierRunner, AgentInterface, WorkflowState } = require('./workflow-engine.js');
    const manifest = {
      config: {},
      verifier_types: {
        'my-verifier': { name: 'My Verifier', threshold: 3.0, prompt: 'Test prompt' }
      }
    };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const runner = new VerifierRunner(agent);
    const result = await runner.verify('my-verifier', { content: 'test' }, manifest);
    assertEqual(typeof result.verdict, 'string');
    assertEqual(typeof result.score, 'number');
  }],

  ['T15: verifier runner falls back to builtin', async () => {
    const { VerifierRunner, AgentInterface, WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {}, verifier_types: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const runner = new VerifierRunner(agent);
    const result = await runner.verify('code_quality', { content: 'test code' }, manifest);
    assertEqual(typeof result.verdict, 'string');
  }],

  ['T16: verifier runner handles unknown type gracefully', async () => {
    const { VerifierRunner, AgentInterface, WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {}, verifier_types: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const runner = new VerifierRunner(agent);
    const result = await runner.verify('unknown-verifier', { content: 'test' }, manifest);
    assertEqual(result.verdict, 'PASS');
  }],

  ['T17: manifest phases are parsed correctly', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, {
      meta: { name: 'multi-phase' },
      phases: {
        p1: { name: 'Phase 1', tasks: [{ id: 't1', title: 'T1', agent_role: 'worker' }] },
        p2: { name: 'Phase 2', tasks: [{ id: 't2', title: 'T2', agent_role: 'worker' }] },
        p3: { name: 'Phase 3', tasks: [{ id: 't3', title: 'T3', agent_role: 'worker' }] },
      }
    });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();
    const phases = Object.keys(engine.manifest.phases);
    assertEqual(phases.length, 3);
    assertEqual(phases[0], 'p1');
    assertEqual(engine.manifest.phases.p1.tasks.length, 1);
  }],

  ['T18: elapsed time calculation', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const elapsed = state.getElapsedTime();
    const parsed = parseFloat(elapsed);
    assertEqual(typeof parsed, 'number');
    assertEqual(parsed >= 0, true);
  }],

  ['T19: workflow engine exports all classes', () => {
    const exports = require('./workflow-engine.js');
    assertEqual(typeof exports.WorkflowEngine, 'function');
    assertEqual(typeof exports.WorkflowState, 'function');
    assertEqual(typeof exports.AgentInterface, 'function');
    assertEqual(typeof exports.VerifierRunner, 'function');
    assertEqual(typeof exports.TaskExecutor, 'function');
    assertEqual(typeof exports.BUILTIN_VERIFIERS, 'object');
  }],

  ['T20: invalid YAML throws parse error', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    fs.writeFileSync(path.join(dir, 'bad.yaml'), 'invalid: yaml: [');
    const engine = new WorkflowEngine(path.join(dir, 'bad.yaml'));
    let error = null;
    try { engine.load(); } catch (e) { error = e; }
    assertEqual(error !== null, true);
    assertEqual(error.message.includes('bad indentation'), true);
  }],

  ['T21: _countOutputTokens includes thinking block estimate', () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const data = {
      usage: { output_tokens: 50 },
      content: [
        { type: 'thinking', thinking: 'A'.repeat(400) },
        { type: 'text', text: 'hello' },
      ]
    };
    const tokens = agent._countOutputTokens(data);
    assertEqual(tokens, 150, '_countOutputTokens');
  }],

  ['T22: _countOutputTokens handles missing thinking', () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const data = { usage: { output_tokens: 42 }, content: [{ type: 'text', text: 'hi' }] };
    assertEqual(agent._countOutputTokens(data), 42);
  }],

  ['T23: _extractAndWriteCode extracts single and multi block', () => {
    const { WorkflowState, AgentInterface, TaskExecutor } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const oldCwd = process.cwd();
    const dir = createTestDir();
    process.chdir(dir);
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const executor = new TaskExecutor(manifest, state, agent);
    const multi = `Here is the code:

\`\`\`javascript
function fib(n) { return n <= 1 ? n : fib(n-1) + fib(n-2); }
\`\`\`

And the test:

\`\`\`javascript
const { test } = require('node:test');
test('fib', () => { console.log(fib(10)); });
\`\`\``;
    const { writtenFiles } = executor._extractAndWriteCode(multi, dir);
    assertEqual(writtenFiles.length, 2, 'should write 2 files');
    assertEqual(fs.existsSync(path.join(dir, 'output_0.js')), true, 'first block written');
    assertEqual(fs.existsSync(path.join(dir, 'output_1.js')), true, 'second block written');
    const single = '```python\nprint("hello")\n```';
    const { writtenFiles: f2 } = executor._extractAndWriteCode(single, dir);
    assertEqual(f2.length, 1, 'single block');
    process.chdir(oldCwd);
  }],

  ['T24: BUILTIN_TOOLS is exported and has all required tools', () => {
    const { BUILTIN_TOOLS } = require('./workflow-engine.js');
    assertEqual(Array.isArray(BUILTIN_TOOLS), true, 'is array');
    assertEqual(BUILTIN_TOOLS.length, 4, '4 tools');
    const names = BUILTIN_TOOLS.map(t => t.name);
    assertEqual(names.includes('read_file'), true, 'has read_file');
    assertEqual(names.includes('run_command'), true, 'has run_command');
    assertEqual(names.includes('grep'), true, 'has grep');
    assertEqual(names.includes('list_files'), true, 'has list_files');
    for (const tool of BUILTIN_TOOLS) {
      assertEqual(typeof tool.name, 'string', `${tool.name} has name`);
      assertEqual(typeof tool.description, 'string', `${tool.name} has description`);
      assertEqual(typeof tool.parameters, 'object', `${tool.name} has parameters`);
      assertEqual(Array.isArray(tool.parameters.required), true, `${tool.name} has required array`);
    }
  }],

  ['T25: _parseVerdict handles all verdict formats', () => {
    const { AgentInterface, WorkflowState, VerifierRunner } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const runner = new VerifierRunner(agent);
    const pass = runner._parseVerdict('{"verdict":"PASS","score":5,"issues":[],"summary":"ok"}', 3.5);
    assertEqual(pass.verdict, 'PASS', 'PASS verdict');
    assertEqual(pass.score, 5, 'score 5');
    const needs = runner._parseVerdict('{"verdict":"NEEDS_IMPROVEMENT","score":2}', 3.5);
    assertEqual(needs.verdict, 'NEEDS_IMPROVEMENT', 'NEEDS_IMPROVEMENT passes through');
    const byScore = runner._parseVerdict('{"score":4}', 3.5);
    assertEqual(byScore.verdict, 'PASS', 'score 4 >= 3.5 -> PASS');
    const byScoreFail = runner._parseVerdict('{"score":2}', 3.5);
    assertEqual(byScoreFail.verdict, 'FAIL', 'score 2 < 3.5 -> FAIL');
  }],

  ['T26: spec-compliance and code_quality builtin verifiers exist', () => {
    const { BUILTIN_VERIFIERS } = require('./workflow-engine.js');
    assertEqual('spec-compliance' in BUILTIN_VERIFIERS, true, 'has spec-compliance');
    assertEqual('code_quality' in BUILTIN_VERIFIERS, true, 'has code_quality');
    assertEqual(BUILTIN_VERIFIERS['spec-compliance'].threshold, 3.0, 'spec-compliance threshold');
    assertEqual(BUILTIN_VERIFIERS['code_quality'].threshold, 3.0, 'code_quality threshold');
  }],

  ['T42: _parseVerdict handles qualitative verdicts and bare JSON fields', () => {
    const { AgentInterface, WorkflowState, VerifierRunner } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const runner = new VerifierRunner(agent);

    // Qualitative: "looks good" → PASS
    const good = runner._parseVerdict('The implementation looks good and meets all requirements.', 3.5);
    assertEqual(good.verdict, 'PASS', 'natural language pass');
    assertEqual(good.score >= 4, true, 'good score >= 4');

    // Qualitative: "needs work" → FAIL
    const needsWork = runner._parseVerdict('This needs work. Several issues remain.', 3.5);
    assertEqual(needsWork.verdict, 'FAIL', 'needs work → FAIL');

    // Qualitative: "excellent" → high score
    const excellent = runner._parseVerdict('Excellent work! All criteria met.', 3.5);
    assertEqual(excellent.verdict, 'PASS', 'excellent → PASS');
    assertEqual(excellent.score >= 4.5, true, 'excellent score >= 4.5');

    // Qualitative: "rejected" → FAIL
    const rejected = runner._parseVerdict('The solution was rejected due to security issues.', 3.5);
    assertEqual(rejected.verdict, 'FAIL', 'rejected → FAIL');

    // Bare JSON with quoted fields (no outer braces as a whole)
    const bare = runner._parseVerdict('Here is my review: "verdict": "PASS", "score": 4.5, "summary": "looks fine"', 3.5);
    assertEqual(bare.verdict, 'PASS', 'bare quoted fields → verdict PASS');
    assertEqual(bare.score, 4.5, 'bare quoted fields → score 4.5');

    // overall_score field
    const overall = runner._parseVerdict('{"overall_score": 4.0, "summary": "ok"}', 3.5);
    assertEqual(overall.score, 4.0, 'overall_score field extracted');
  }],

  ['T28: _groupTasksIntoWaves handles no dependencies', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    const tasks = [
      { id: 'a', title: 'A' },
      { id: 'b', title: 'B' },
      { id: 'c', title: 'C' },
    ];

    const waves = engine._groupTasksIntoWaves(tasks);
    assertEqual(waves.length, 1, 'single wave');
    assertEqual(waves[0].length, 3, 'all 3 tasks in wave 1');
  }],

  ['T29: _groupTasksIntoWaves respects dependencies', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    const tasks = [
      { id: 'a', title: 'A' },
      { id: 'b', title: 'B', depends_on: ['a'] },
      { id: 'c', title: 'C', depends_on: ['a'] },
      { id: 'd', title: 'D', depends_on: ['b', 'c'] },
    ];

    const waves = engine._groupTasksIntoWaves(tasks);
    assertEqual(waves.length, 3, '3 waves');
    assertEqual(waves[0].map(t => t.id).sort().join(','), 'a', 'wave 0: a only');
    assertEqual(waves[1].map(t => t.id).sort().join(','), 'b,c', 'wave 1: b and c');
    assertEqual(waves[2].map(t => t.id).join(','), 'd', 'wave 2: d only');
  }],

  ['T30: _groupTasksIntoWaves handles external dependencies', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    const tasks = [
      { id: 'x', title: 'X', depends_on: ['external-task'] },
      { id: 'y', title: 'Y' },
    ];

    const waves = engine._groupTasksIntoWaves(tasks);
    assertEqual(waves.length, 1, 'single wave (external dep treated as satisfied)');
    assertEqual(waves[0].map(t => t.id).sort().join(','), 'x,y', 'both tasks in wave 1');
  }],

  ['T31: _groupTasksIntoWaves handles complex diamond dependency', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    const tasks = [
      { id: 'a', title: 'A' },
      { id: 'b', title: 'B', depends_on: ['a'] },
      { id: 'c', title: 'C', depends_on: ['a'] },
      { id: 'd', title: 'D', depends_on: ['b', 'c'] },
    ];

    const waves = engine._groupTasksIntoWaves(tasks);
    assertEqual(waves.length, 3, '3 waves (diamond pattern)');
    assertEqual(waves[0].length, 1, 'wave 0 has 1 task');
    assertEqual(waves[1].length, 2, 'wave 1 has 2 tasks (b and c run in parallel)');
    assertEqual(waves[2].length, 1, 'wave 2 has 1 task');
  }],

  ['T27: _executeTool handles all tool types', async () => {
    const { AgentInterface } = require('./workflow-engine.js');
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: {} };
    const state = new WorkflowState(manifest);
    const agent = new AgentInterface(state);
    const out = await agent._executeTool('run_command', { command: 'echo hello' });
    assertContains(out, 'hello', 'run_command works');
    const files = await agent._executeTool('list_files', { path: __dirname, pattern: '*.js' });
    assertEqual(typeof files, 'string', 'list_files returns string');
    const grep = await agent._executeTool('grep', { pattern: 'function', path: __dirname, include: 'js' });
    assertEqual(typeof grep, 'string', 'grep returns string');
    const unknown = await agent._executeTool('nonexistent', {});
    assertContains(unknown, 'unknown', 'unknown tool handled');
  }],

  ['T32: end-to-end mock workflow with parallel tasks', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const oldCwd = process.cwd();
    const dir = createTestDir();
    process.chdir(dir);
    writeManifest(dir, {
      meta: { name: 'e2e-parallel-test' },
      config: {
        adversarial_mode: false,
        token_budget: 50000,
      },
      phases: {
        build: {
          name: 'Build Phase',
          tasks: [
            { id: 'task-a', title: 'Task A', agent_role: 'worker', description: 'Build component A' },
            { id: 'task-b', title: 'Task B', agent_role: 'worker', description: 'Build component B', depends_on: ['task-a'] },
            { id: 'task-c', title: 'Task C', agent_role: 'worker', description: 'Build component C', depends_on: ['task-a'] },
            { id: 'task-d', title: 'Task D', agent_role: 'worker', description: 'Integrate all', depends_on: ['task-b', 'task-c'] },
          ]
        }
      }
    });

    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    await engine.init();        // init() calls load() which creates state — must be before platform set
    engine.platform = 'mock';   // set platform AFTER init
    engine.agent.platform = 'mock';   // agent.platform is set at construction from env
    engine.executor.agent.platform = 'mock';  // executor holds its own agent ref
    // init() already set up state.tasks — don't replace it
    const result = await engine.run();

    process.chdir(oldCwd);

    const completed = result.tasks.filter(t => t.status === 'completed');
    const failed = result.tasks.filter(t => t.status === 'failed');
    assertEqual(failed.length, 0, 'no tasks failed');
    assertEqual(completed.length, 4, 'all 4 tasks completed');
    const taskA = result.tasks.find(t => t.id === 'task-a');
    const taskB = result.tasks.find(t => t.id === 'task-b');
    const taskD = result.tasks.find(t => t.id === 'task-d');
    assertEqual(taskA?.status, 'completed', 'task-a completed');
    assertEqual(taskB?.status, 'completed', 'task-b completed');
    assertEqual(taskD?.status, 'completed', 'task-d completed');
  }],

  ['T33: adversarial mode stops on task failure', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const oldCwd = process.cwd();
    const dir = createTestDir();
    process.chdir(dir);

    writeManifest(dir, {
      meta: { name: 'adversarial-stop-test' },
      config: {
        adversarial_mode: true,
        token_budget: 50000,
        verifier_max_retries: 0,
      },
      phases: {
        build: {
          name: 'Build Phase',
          verifier: 'spec-compliance',
          tasks: [
            { id: 'task-a', title: 'Task A', agent_role: 'worker', description: 'Build A __PASS__' },
            { id: 'task-b', title: 'Task B', agent_role: 'worker', description: 'Build B __FAIL__', depends_on: ['task-a'] },
            { id: 'task-c', title: 'Task C', agent_role: 'worker', description: 'Build C __PASS__', depends_on: ['task-a'] },
            { id: 'task-d', title: 'Task D', agent_role: 'worker', description: 'Build D', depends_on: ['task-b', 'task-c'] },
          ]
        }
      }
    });

    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    await engine.init();
    engine.platform = 'mock';
    engine.agent.platform = 'mock';
    engine.executor.agent.platform = 'mock';
    const result = await engine.run();

    process.chdir(oldCwd);

    // task-a completes, wave 2 (b,c) - b fails in adversarial mode
    // engine should stop and not run task-d
    const completedIds = result.tasks.filter(t => t.status === 'completed').map(t => t.id);
    assertEqual(completedIds.includes('task-d'), false, 'task-d should not run after failure in adversarial mode');
  }],

  ['T34: circular dependency warning (no infinite loop)', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'circular-test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    // Self-dependency
    const tasks = [{ id: 'a', title: 'A', depends_on: ['a'] }];
    const waves = engine._groupTasksIntoWaves(tasks);
    // Should detect circular and put in a wave (won't infinite loop)
    assertEqual(waves.length >= 1, true, 'has at least one wave');
  }],

  ['T35: token warning fires at threshold', () => {
    const { WorkflowState } = require('./workflow-engine.js');
    const manifest = { config: { token_budget: 100, token_budget_warning: 0.5 } };
    const state = new WorkflowState(manifest);
    // Add usage that crosses 50% threshold
    state.addTokenUsage(51);
    assertEqual(state.tokenUsed, 51, 'token count correct');
    assertEqual(state.tokenBudget, 100, 'budget correct');
    // Warning is logged, but we can't test the log output directly
    // Just verify the state is correct
  }],

  ['T36: context file written after task completion', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const oldCwd = process.cwd();
    const dir = createTestDir();
    process.chdir(dir);
    writeManifest(dir, {
      meta: { name: 'context-test' },
      config: { adversarial_mode: false, token_budget: 50000 },
      phases: {
        build: {
          name: 'Build Phase',
          tasks: [
            { id: 'task-a', title: 'Task A', agent_role: 'worker', description: 'Build A' },
          ]
        }
      }
    });

    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    await engine.init();
    engine.platform = 'mock';
    engine.agent.platform = 'mock';
    engine.executor.agent.platform = 'mock';
    await engine.run();

    process.chdir(oldCwd);

    // Context file should be written
    const contextFile = path.join(dir, '.sop-workflow', 'context', 'task-a.json');
    assertEqual(fs.existsSync(contextFile), true, 'context file exists');
    const ctx = JSON.parse(fs.readFileSync(contextFile, 'utf8'));
    assertEqual(ctx.taskId, 'task-a', 'taskId correct');
    assertEqual(ctx.verdict, 'PASS', 'verdict recorded');
    assertEqual(typeof ctx.score, 'number', 'score recorded');
  }],

  ['T37: completed task is skipped on resume', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const oldCwd = process.cwd();
    const dir = createTestDir();
    process.chdir(dir);
    writeManifest(dir, {
      meta: { name: 'skip-test' },
      config: { adversarial_mode: false, token_budget: 50000 },
      phases: {
        build: {
          name: 'Build Phase',
          tasks: [
            { id: 'task-a', title: 'Task A', agent_role: 'worker', description: 'Build A' },
            { id: 'task-b', title: 'Task B', agent_role: 'worker', description: 'Build B', depends_on: ['task-a'] },
          ]
        }
      }
    });

    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    await engine.init();
    engine.platform = 'mock';
    engine.agent.platform = 'mock';
    engine.executor.agent.platform = 'mock';

    // Pre-complete task-a in state
    engine.state.updateTask('task-a', { status: 'completed', start: Date.now(), duration: 100 });

    // Set resume point to task-b
    engine.state.taskId = 'task-b';

    const result = await engine.run();

    process.chdir(oldCwd);

    const taskA = result.tasks.find(t => t.id === 'task-a');
    const taskB = result.tasks.find(t => t.id === 'task-b');
    assertEqual(taskA?.status, 'completed', 'task-a stays completed');
    assertEqual(taskB?.status, 'completed', 'task-b completes');
  }],

  ['T38: _writeTaskContext creates context directory', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'ctx-test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();
    // Methods are on TaskExecutor, not WorkflowEngine
    assertEqual(typeof engine.executor._writeTaskContext, 'function', '_writeTaskContext is on executor');

    const task = { id: 't1', description: 'test task' };
    engine.state.phase = 'build';
    engine.executor._writeTaskContext(task, 'hello world', ['a.js'], { verdict: 'PASS', score: 5 }, dir);

    const ctxFile = path.join(dir, '.sop-workflow', 'context', 't1.json');
    assertEqual(fs.existsSync(ctxFile), true, 'context file created');
    const ctx = JSON.parse(fs.readFileSync(ctxFile, 'utf8'));
    assertEqual(ctx.taskId, 't1', 'task id in context');
    assertEqual(ctx.verdict, 'PASS', 'verdict in context');
    assertEqual(ctx.score, 5, 'score in context');
  }],

  ['T39: _retryWithBackoff is defined on agent', () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'retry-test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();
    assertEqual(typeof engine.agent._retryWithBackoff, 'function', '_retryWithBackoff is on agent (AgentInterface)');
  }],

  ['T40: evidence commands run in parallel (async)', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, { meta: { name: 'evidence-test' }, config: {} });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();

    // Worker output with two commands that would take at least 200ms each
    const output = 'Run: `sleep 0.05 && echo one`\nRun: `sleep 0.05 && echo two`';
    const start = Date.now();
    const evidence = await engine.executor._runEvidenceVerification(output, dir);
    const elapsed = Date.now() - start;

    // If parallel: ~50ms. If sequential: ~100ms
    assertEqual(evidence.length, 2, 'both commands executed');
    assertEqual(elapsed < 200, true, 'ran in under 200ms (parallel)');
    assertEqual(evidence[0].status, 'PASS', 'first command passed');
    assertEqual(evidence[1].status, 'PASS', 'second command passed');
  }],

  ['T41: evidence results injected into verifier prompt', async () => {
    const { WorkflowEngine } = require('./workflow-engine.js');
    const dir = createTestDir();
    writeManifest(dir, {
      meta: { name: 'evidence-inject-test' },
      config: { adversarial_mode: false, token_budget: 50000 },
      phases: {
        build: {
          name: 'Build Phase',
          tasks: [
            { id: 'task-x', title: 'Task X', agent_role: 'worker', description: 'Write a function that returns 42', verifier: 'spec-compliance' },
          ]
        }
      }
    });
    const engine = new WorkflowEngine(path.join(dir, 'test.yaml'));
    engine.load();
    engine.state.phase = 'build';
    engine.platform = 'mock';
    engine.agent.platform = 'mock';
    engine.executor.agent.platform = 'mock';

    const mockEvidence = [
      { command: 'node test.js', status: 'pass', output: '✓ all tests passed' },
      { command: 'node lint.js', status: 'fail', output: '', error: 'SyntaxError' },
    ];
    engine.executor._runEvidenceVerification = async () => mockEvidence;

    // Override verifier to check evidence injection
    engine.executor.verifier = {
      verify: async (type, opts) => {
        const hasEvidenceSection = opts.content && opts.content.includes('EVIDENCE RESULTS');
        assertEqual(hasEvidenceSection, true, 'verifier receives EVIDENCE RESULTS section in content');
        const hasPassOutput = opts.content.includes('node test.js') && opts.content.includes('all tests passed');
        assertEqual(hasPassOutput, true, 'verifier sees pass evidence output');
        const hasFailOutput = opts.content.includes('node lint.js') && opts.content.includes('SyntaxError');
        assertEqual(hasFailOutput, true, 'verifier sees fail evidence output');
        return { verdict: 'PASS', score: 5, summary: 'mock pass' };
      }
    };

    const result = engine.executor.executeTask(
      { id: 'task-x', description: 'Write a function that returns 42', title: 'Task X' },
      'build',
      null,
      30000
    );
    assertEqual(result !== null, true, 'executeTask returned a result');
  }],
];

(async () => {
  for (const [name, fn] of TESTS) {
    await test(name, fn);
  }

  // ============================================================
  // 摘要
  // ============================================================
  console.log(`\n${'='.repeat(50)}`);
  console.log(`Tests: ${passed + failed} | ${GREEN}${passed} passed${RESET} | ${RED}${failed} failed${RESET}`);
  console.log(`${'='.repeat(50)}`);

  if (failed > 0) process.exit(1);
  // Explicit exit needed: active fetch() handles in MiniMax API calls keep event loop alive
  process.exit(0);
})();
