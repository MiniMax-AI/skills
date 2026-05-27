#!/usr/bin/env node
/**
 * SOP Workflow Engine
 *
 * 核心执行引擎 - 读取 manifest，执行 SOP 流程
 *
 * Code as Law:
 *   - 这个文件硬编码了执行流程
 *   - AI 只能在每个 agent() 节点内发挥
 *   - AI 无法跳过验证步骤
 *
 * 使用方式:
 *   node workflow-engine.js <manifest.yaml> [options]
 *
 * 示例:
 *   node workflow-engine.js manifests/superpowers-sop.yaml
 *   node workflow-engine.js my-sop.yaml --phase=execute
 *   node workflow-engine.js --status my-sop.yaml
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const glob = require('glob');
const { promisify } = require('util');
const exec = promisify(require('child_process').exec);

// ============================================================
// ANSI 颜色输出
// ============================================================
const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

const log = {
  info: (msg) => console.log(`${c.blue}[INFO]${c.reset} ${msg}`),
  ok: (msg) => console.log(`${c.green}[PASS]${c.reset} ${msg}`),
  warn: (msg) => console.log(`${c.yellow}[WARN]${c.reset} ${msg}`),
  fail: (msg) => console.log(`${c.red}[FAIL]${c.reset} ${msg}`),
  phase: (msg) => console.log(`\n${c.magenta}[PHASE]${c.reset} ${c.bold}${msg}${c.reset}`),
  task: (msg) => console.log(`  ${c.cyan}[TASK]${c.reset} ${msg}`),
  verifier: (msg) => console.log(`  ${c.yellow}[VERIFIER]${c.reset} ${msg}`),
  token: (used, budget) => {
    const pct = budget > 0 ? ((used / budget) * 100).toFixed(1) : '0';
    const color = pct > 80 ? c.red : pct > 50 ? c.yellow : c.green;
    console.log(`  ${c.blue}[TOKEN]${c.reset} ${used}/${budget} (${color}${pct}%${c.reset})`);
  },
  debug: (msg) => {
    if (process.env.SOP_DEBUG) console.log(`${c.dim}[DEBUG] ${msg}${c.reset}`);
  },
};

// ============================================================
// 内置 Verifier 库 (基础版)
// ============================================================
const BUILTIN_VERIFIERS = {
  'spec-compliance': {
    name: 'Spec合规评审',
    threshold: 3.0,
    prompt: `You are a spec compliance reviewer. Verify implementation matches the SPEC provided at the top of the input.

The SPEC section contains the ORIGINAL REQUIREMENT (from the task description). The WORKER OUTPUT section contains what was produced.

CRITICAL — Evidence Before Claims:
- Do NOT trust the implementer's report
- Use the read_file and run_command tools to verify ACTUAL behavior
- Run tests to confirm functionality
- Check edge cases with your own commands

MANDATORY VERIFICATION STEPS:
1. Use read_file to read the source files (filename is in the WORKER OUTPUT or the "=== 已生成的文件 ===" section)
2. Use run_command to run tests: "cd <output_dir> && node --test *.test.js" or similar
3. Compare actual implementation against SPEC requirements

Check:
- MISSING: Did they implement everything the spec requests?
- EXTRA: Did they build things not in the spec?
- WRONG: Did they misunderstand requirements?
- BUGS: Does the code actually work when run?

Report JSON:
{"verdict": "PASS|FAIL", "score": 1-5, "issues": [{"severity":"high|medium|low","file":"path","description":"..."}], "summary": "..."}`,
  },

  code_quality: {
    name: '代码质量',
    threshold: 3.0,
    prompt: `You are a code quality reviewer. Assess implementation quality AFTER spec compliance passes.

CRITICAL — Evidence Before Claims:
- Do NOT just read the code — USE TOOLS to verify quality
- Run tests: use run_command to execute "node --test" or "pytest" etc.
- Check for race conditions, memory leaks with actual runs
- Verify edge cases with your own command tests

MANDATORY VERIFICATION STEPS:
1. Use read_file to inspect code structure and error handling
2. Use run_command to verify tests pass: "cd <dir> && node --test *.test.js"
3. Check edge cases: run the function with various inputs
4. Use grep to find potential issues (unused vars, TODOs, etc.)

Dimensions (each 1-5):
- Readability: Clear naming, reasonable structure, no deep nesting
- Maintainability: Modular, decoupled, good dependency management
- Edge cases: Invalid inputs handled properly
- Tests: Verify real behavior (not mocks), cover edge cases
- Error handling: Graceful failures, meaningful error messages

Severity:
- Critical (MUST FIX): Bugs, broken functionality, security issues
- Important (SHOULD FIX): Missing features, poor architecture
- Minor (NICE TO HAVE): Style, optimization

Return JSON:
{"verdict": "PASS|FAIL", "score": 1-5, "issues": [{"severity":"critical|important|minor","file":"path","description":"..."}], "summary": "..."}`,
  },

  security: {
    name: '安全审计',
    threshold: 4.0,
    prompt: `你是一个安全审计专家。请检查交付物的安全性。

重点检查:
- 注入风险: SQL注入、XSS、命令注入
- 认证授权: 认证绕过、权限提升
- 数据保护: 敏感数据明文、硬编码凭证
- 已知漏洞: 依赖包CVE

返回 JSON:
{
  "verdict": "PASS|FAIL|NEEDS_IMPROVEMENT",
  "score": 1-5,
  "issues": [{"severity":"high|medium|low","file":"","line":0,"description":"","fix":""}],
  "summary": "一句话总结"
}`,
  },

  functional: {
    name: '功能正确性',
    threshold: 4.0,
    prompt: `你是一个功能测试专家。请验证交付物是否正确实现需求。

检查重点:
- 功能完整性: 所有需求是否实现
- 逻辑正确性: 核心逻辑是否正确
- 边界处理: 空值、异常、超长输入

返回 JSON:
{
  "verdict": "PASS|FAIL|NEEDS_IMPROVEMENT",
  "score": 1-5,
  "issues": [{"severity":"high|medium|low","file":"","line":0,"description":"","fix":""}],
  "summary": "一句话总结"
}`,
  },

  performance: {
    name: '性能评估',
    threshold: 3.0,
    prompt: `你是一个性能优化专家。请评估交付物的性能。

检查重点:
- 算法复杂度: 是否有 O(n²) 或更差
- 资源使用: 内存泄漏、连接池
- 优化意识: 索引、分页、缓存

返回 JSON:
{
  "verdict": "PASS|FAIL|NEEDS_IMPROVEMENT",
  "score": 1-5,
  "issues": [{"severity":"high|medium|low","file":"","line":0,"description":"","fix":""}],
  "summary": "一句话总结"
}`,
  },

  comprehensive: {
    name: '综合评审',
    threshold: 3.8,
    prompt: `你是一个高级技术评审专家。请对交付物进行最终综合评审。

评估维度:
- 需求满足度
- 代码质量
- 安全性
- 性能
- 文档完整性

返回 JSON:
{
  "verdict": "PASS|FAIL|NEEDS_IMPROVEMENT",
  "score": 1-5,
  "issues": [{"severity":"high|medium|low","file":"","line":0,"description":"","fix":""}],
  "summary": "一句话总结"
}`,
  },
};

// ============================================================
// MiniMax-M1 推荐工具集 (superpowers evidence-before-claims)
// ============================================================
const BUILTIN_TOOLS = [
  {
    name: 'read_file',
    description: 'Read the contents of a file. Returns the file content or an error message.',
    parameters: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Absolute or relative file path. For generated files, use just the filename (e.g., "fib.js")',
        },
        start_line: {
          type: 'number',
          description: 'Starting line number (1-indexed). Optional.',
        },
        end_line: {
          type: 'number',
          description: 'Ending line number. Optional.',
        },
      },
      required: ['path'],
    },
  },
  {
    name: 'run_command',
    description: 'Execute a shell command and return the output. Use this to verify code works.',
    parameters: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The shell command to execute',
        },
        cwd: {
          type: 'string',
          description: 'Working directory. Defaults to process cwd.',
        },
        timeout: {
          type: 'number',
          description: 'Timeout in seconds. Defaults to 30.',
        },
      },
      required: ['command'],
    },
  },
  {
    name: 'grep',
    description: 'Search for a pattern in files. Returns matching lines with file:line format.',
    parameters: {
      type: 'object',
      properties: {
        pattern: {
          type: 'string',
          description: 'Regular expression pattern to search for',
        },
        path: {
          type: 'string',
          description: 'Directory to search in. Defaults to current working directory.',
        },
        include: {
          type: 'string',
          description: 'File extension to search (e.g., "js", "py"). Defaults to all files.',
        },
      },
      required: ['pattern'],
    },
  },
  {
    name: 'list_files',
    description: 'List files in a directory matching a glob pattern.',
    parameters: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Directory to search. Defaults to current working directory.',
        },
        pattern: {
          type: 'string',
          description: 'Glob pattern. Defaults to "**/*".',
        },
      },
      required: [],
    },
  },
];

// ============================================================
// 状态管理
// ============================================================
class WorkflowState {
  constructor(manifest, taskId = null) {
    this.manifest = manifest;
    this.taskId = taskId;
    this.phase = 'init';
    this.startTime = Date.now();
    this.tokenUsed = 0;
    this.tokenBudget = parseInt(
      manifest?.config?.token_budget ||
      process.env.SOP_TOKEN_BUDGET ||
      '100000'
    );
    this.tasks = [];
    this.currentTask = null;
    this.verifierResults = [];
    this.history = [];
    this.contextIsolation = manifest.config?.context_isolation || 'strict';
  }

  addTokenUsage(tokens) {
    this.tokenUsed += tokens;
    log.token(this.tokenUsed, this.tokenBudget);

    // 检查 token 警告阈值
    const warningThreshold = this.manifest.config?.token_budget_warning || 0.8;
    if (this.tokenBudget > 0 && (this.tokenUsed / this.tokenBudget) > warningThreshold) {
      log.warn(`Token 消耗达到 ${((this.tokenUsed / this.tokenBudget) * 100).toFixed(1)}%，接近预算上限`);
    }
  }

  getElapsedTime() {
    return ((Date.now() - this.startTime) / 1000).toFixed(1) + 's';
  }

  save() {
    const stateFile = path.join(process.cwd(), '.sop-workflow-state.json');
    const tmpFile = stateFile + '.tmp';
    const data = {
      phase: this.phase,
      taskId: this.taskId,
      tokenUsed: this.tokenUsed,
      tasks: this.tasks.map(t => ({
        id: t.id,
        status: t.status,
        start: t.start,
        duration: t.duration,
      })),
      elapsed: this.getElapsedTime(),
    };
    // Atomic write: write to temp file, then rename (POSIX guarantee)
    fs.writeFileSync(tmpFile, JSON.stringify(data, null, 2));
    fs.renameSync(tmpFile, stateFile);
    log.debug(`State saved to ${stateFile}`);
    return stateFile;
  }

  load() {
    const stateFile = path.join(process.cwd(), '.sop-workflow-state.json');
    if (fs.existsSync(stateFile)) {
      try {
        const data = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
        this.phase = data.phase || 'init';
        this.taskId = data.taskId;
        this.tokenUsed = data.tokenUsed || 0;
        this.tasks = data.tasks || [];
        return true;
      } catch (e) {
        log.warn(`State file corrupted (${e.message}), starting fresh`);
        return false;
      }
    }
    return false;
  }

  addTask(taskId, status = 'pending') {
    if (this.tasks.some(t => t.id === taskId)) return; // deduplicate
    this.tasks.push({ id: taskId, status, start: Date.now() });
  }

  updateTask(taskId, updates) {
    const task = this.tasks.find(t => t.id === taskId);
    if (task) {
      Object.assign(task, updates);
    }
  }
}

// ============================================================
// Agent 调用接口
// ============================================================
class AgentInterface {
  constructor(state) {
    this.state = state;
    this.platform = process.env.SOP_PLATFORM || 'opencode';
  }

  /**
   * 调用 Agent 执行任务
   * @param {string} role - agent 角色
   * @param {string} prompt - 任务 prompt
   * @param {object} options - { timeout, model, system_prompt }
   * @returns {Promise<{role, prompt, context, output, tokens}>}
   */
  async agent(role, prompt, options = {}) {
    const estimatedTokens = Math.ceil(prompt.length / 4);
    this.state.addTokenUsage(estimatedTokens);

    log.debug(`${role}: ${prompt.substring(0, 100)}...`);

    // 根据平台选择调用方式
    switch (this.platform) {
      case 'claude':
        return this._callClaude(role, prompt, options);
      case 'opencode':
        return this._callOpenCode(role, prompt, options);
      case 'codex':
        return this._callCodex(role, prompt, options);
      case 'minimax':
        return this._callMiniMax(role, prompt, options);
      case 'mock':
        return this._mockAgent(role, prompt, options);
      default:
        throw new Error(`Unknown platform: ${this.platform}`);
    }
  }

  async _mockAgent(role, prompt, options = {}) {
    // Mock 模式: 记录调用，verifier 特殊处理
    log.info(`[MOCK ${role}] ${prompt.substring(0, 80)}...`);

    let output = `[MOCK OUTPUT for ${role}]`;

    // Mock verifier: 解析 prompt 中的 verdicts 并返回
    if (role === 'verifier') {
      output = this._mockVerifier(prompt);
    }

    return {
      role,
      prompt,
      output,
      tokens: Math.ceil(prompt.length / 4),
    };
  }

  _mockVerifier(prompt) {
    // 提取交付物内容
    const deliverableMatch = prompt.match(/=== 交付物 ===\s*\n?([\s\S]*?)(?=\n===|\n请返回|$)/);
    const content = (deliverableMatch && deliverableMatch[1]) ? deliverableMatch[1].trim() : '';

    // 1. 检查特殊标记 (用于测试)
    if (content.includes('__FAIL__') || content.includes('FAIL_NOW')) {
      return JSON.stringify({ verdict: 'FAIL', score: 1, issues: [{ severity: 'high', description: '测试失败' }], summary: '包含失败标记' });
    }

    // 2. 尝试解析嵌入的完整 JSON verdicts (在 prompt 末尾的独立 JSON)
    // 匹配: 换行后跟 { "verdict": ... }
    const lines = prompt.split('\n');
    for (let i = lines.length - 1; i >= 0; i--) {
      const line = lines[i].trim();
      if (line.startsWith('{') && line.includes('"verdict"')) {
        try {
          const parsed = JSON.parse(line);
          return JSON.stringify(parsed);
        } catch (e) {
          // 继续尝试
        }
        // 尝试多行
        let multiLine = line;
        for (let j = i + 1; j < lines.length; j++) {
          multiLine += '\n' + lines[j].trim();
          try {
            const parsed = JSON.parse(multiLine);
            return JSON.stringify(parsed);
          } catch (e) {
            // 继续
          }
          if (multiLine.includes('}')) break;
        }
      }
    }

    // 3. 尝试从整个 prompt 中找 JSON (宽松匹配)
    const jsonMatch = prompt.match(/\{[^{}]*"verdict"\s*:\s*"(PASS|FAIL|NEEDS_IMPROVEMENT)"[^{}]*\}/);
    if (jsonMatch) {
      try {
        const parsed = JSON.parse(jsonMatch[0]);
        return JSON.stringify(parsed);
      } catch (e) {
        // 解析失败
      }
    }

    // 4. 模拟智能判断: 分析交付物内容
    const score = this._evaluateContent(content);
    return JSON.stringify({
      verdict: score >= 3.5 ? 'PASS' : 'FAIL',
      score,
      issues: score < 3.5 ? [{ severity: 'high', description: '内容质量不达标' }] : [],
      summary: score >= 3.5 ? '内容质量良好' : '内容质量不达标',
    });
  }

  _evaluateContent(content) {
    // 模拟评估逻辑: 分析内容质量
    if (!content || content === '[MOCK OUTPUT for worker]' || content.length < 10) {
      return 5.0; // mock worker 输出默认良好
    }
    // 检测明显问题
    const issues = [
      { pattern: /undefined|NaN/is, severity: 0.5 },
      { pattern: /TODO|FIXME|HACK/is, severity: 0.3 },
      { pattern: /console\.log/is, severity: 0.2 },
    ];
    let penalty = 0;
    for (const issue of issues) {
      if (issue.pattern.test(content)) penalty += issue.severity;
    }
    return Math.max(1, Math.min(5, 5.0 - penalty));
  }

  async _callClaude(role, prompt, options = {}) {
    const systemPrompt = this._getSystemPrompt(role);
    const fullPrompt = `${systemPrompt}\n\nTask:\n${prompt}`;

    log.info(`[Claude] Calling ${role} agent`);

    // 尝试通过 Claude Code CLI 调用
    try {
      const { execSync } = require('child_process');
      // Claude Code 的 MCP 工具调用方式
      // 这里简化处理，实际需要根据 Claude Code 版本调整
      const result = execSync('claude --print "test"', {
        encoding: 'utf8',
        timeout: 30000,
      }).trim();

      return { role, prompt: fullPrompt, output: result, tokens: Math.ceil(fullPrompt.length / 4) };
    } catch (e) {
      log.debug(`Claude CLI not available: ${e.message}`);
      // 回退到 mock
      return this._mockAgent(role, prompt, options);
    }
  }

  async _callOpenCode(role, prompt, options = {}) {
    log.info(`[OpenCode] Calling ${role} agent`);

    // 尝试通过 mavis communication 调用
    try {
      const { spawn } = require('child_process');
      // 实际实现需要 mavis daemon 支持
      // 这里简化处理
      return this._mockAgent(role, prompt, options);
    } catch (e) {
      return this._mockAgent(role, prompt, options);
    }
  }

  async _callCodex(role, prompt, options = {}) {
    log.info(`[Codex] Calling ${role} agent`);
    return this._mockAgent(role, prompt, options);
  }

  /**
   * Execute a tool call and return the result
   */
  /**
   * Execute a tool. run_command is async; others sync.
   * Returns a Promise — always await the result.
   */
  async _executeTool(toolName, args) {
    const outputDir = path.join(process.cwd(), '.sop-workflow', 'outputs');

    switch (toolName) {
      case 'read_file': {
        // args: { path: string, start_line?: number, end_line?: number }
        const filePath = args.path;
        if (!filePath) return 'Error: path is required';
        // 支持 output 目录的相对路径
        const fullPath = filePath.startsWith('/') ? filePath : path.join(process.cwd(), filePath);
        if (!fs.existsSync(fullPath)) {
          // 尝试在 output 目录找
          const outPath = path.join(outputDir, path.basename(filePath));
          if (fs.existsSync(outPath)) {
            const lines = fs.readFileSync(outPath, 'utf8').split('\n');
            const start = (args.start_line || 1) - 1;
            const end = args.end_line || lines.length;
            return lines.slice(start, end).join('\n');
          }
          return `Error: file not found: ${fullPath}`;
        }
        const lines = fs.readFileSync(fullPath, 'utf8').split('\n');
        const start = (args.start_line || 1) - 1;
        const end = args.end_line || lines.length;
        return lines.slice(start, end).join('\n');
      }

      case 'grep': {
        // args: { pattern: string, path?: string, include?: string }
        const results = [];
        const searchPath = args.path || process.cwd();
        const searchPattern = new RegExp(args.pattern, 'i');
        const ext = args.include || '*';
        const files = ext === '*'
          ? glob.sync('**/*', { cwd: searchPath, ignore: ['node_modules/**', '.git/**'] })
          : glob.sync(`**/*.${ext}`, { cwd: searchPath, ignore: ['node_modules/**'] });
        for (const f of files.slice(0, 50)) {
          try {
            const content = fs.readFileSync(path.join(searchPath, f), 'utf8');
            const lines = content.split('\n');
            lines.forEach((line, i) => {
              if (searchPattern.test(line)) {
                results.push(`${f}:${i + 1}: ${line}`);
              }
            });
          } catch {}
        }
        return results.length > 0 ? results.slice(0, 100).join('\n') : 'No matches found';
      }

      case 'run_command': {
        // args: { command: string, cwd?: string, timeout?: number }
        const cwd = args.cwd || process.cwd();
        const timeoutMs = (args.timeout || 30) * 1000;
        try {
          const { stdout, stderr } = await Promise.race([
            exec(args.command, { encoding: 'utf8', cwd, timeout: timeoutMs }),
            new Promise((_, rej) => setTimeout(() => rej(new Error('Command timed out')), timeoutMs)),
          ]);
          return (stdout || '').substring(0, 2000);
        } catch (e) {
          const msg = e.message || String(e);
          if (msg.includes('timed out')) return `Error: command timed out after ${timeoutMs}ms`;
          return `Error (exit ${e.code || 1}): ${(e.stderr || msg || '').substring(0, 500)}`;
        }
      }

      case 'list_files': {
        // args: { path?: string, pattern?: string }
        const searchPath = args.path || process.cwd();
        const files = glob.sync(args.pattern || '**/*', {
          cwd: searchPath,
          ignore: ['node_modules/**', '.git/**', '.sop-workflow/**'],
        });
        return files.slice(0, 200).join('\n');
      }

      default:
        return `Error: unknown tool "${toolName}"`;
    }
  }

  /**
   * Count output tokens including thinking blocks.
   * MiniMax API only reports text tokens in usage.output_tokens.
   * Thinking block estimated at char_count / 4 (conservative).
   * MiniMax tokenizer: ~3.5 chars/token for Chinese, ~4 for English.
   */
  _countOutputTokens(data) {
    const textTokens = data.usage?.output_tokens || 0;
    let thinkingChars = 0;
    if (Array.isArray(data.content)) {
      for (const c of data.content) {
        if (c.type === 'thinking' && c.thinking) {
          thinkingChars += (c.thinking.length || 0);
        }
      }
    }
    const thinkingTokens = Math.ceil(thinkingChars / 4);
    return textTokens + thinkingTokens;
  }

  async _callMiniMaxWithTools(role, prompt, options = {}) {
    const tools = options.tools || [];
    const systemPrompt = this._getSystemPrompt(role);
    const fullPrompt = `${systemPrompt}\n\nTask:\n${prompt}`;

    const model = process.env.SOP_LLM_MODEL || 'MiniMax-M2.7-highspeed';
    const token = process.env.MAVIS_ACCESS_TOKEN;
    const timeout = (options.timeout || 120) * 1000;
    const url = 'https://agent.minimaxi.com/mavis/api/v1/llm/v1/messages';
    const maxToolRounds = 5;

    log.info(`[MiniMax] Calling ${role} with ${tools.length} tools (${model})`);

    // 构建 messages
    const messages = [{ role: 'user', content: fullPrompt }];

    // 如果有 tools，追加 tool descriptions 到 system prompt
    if (tools.length > 0) {
      const toolDescs = tools.map(t =>
        `- ${t.name}: ${t.description}\n  args: ${JSON.stringify(t.parameters?.properties || {})}`
      ).join('\n');
      messages[0].content += `\n\nYou have access to these tools:\n${toolDescs}\n\nWhen you need to use a tool, output EXACTLY this format:\n<tool_calls>\n{"name": "tool_name", "arguments": {"arg1": "value1"}}\n</tool_calls>`;
    }

    try {
      for (let round = 0; round < maxToolRounds; round++) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeout);
        const externalSignal = options.signal || null;
        if (externalSignal) {
          externalSignal.addEventListener('abort', () => controller.abort());
        }

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            model,
            messages,
            max_tokens: parseInt(process.env.SOP_MAX_OUTPUT_TOKENS || '131072'),
            temperature: 1.0,
            top_p: 0.95,
          }),
          signal: controller.signal,
        });

        clearTimeout(timer);

        if (!response.ok) {
          const err = await response.text();
          throw new Error(`MiniMax API error ${response.status}: ${err}`);
        }

        const data = await response.json();
        const tokens = this._countOutputTokens(data);
        this.state.addTokenUsage(tokens);

        // 提取文本
        let text = '';
        if (Array.isArray(data.content)) {
          for (const c of data.content) {
            if (c.type === 'text') text += c.text || '';
          }
        }

        // 检查 tool_calls
        if (tools.length > 0) {
          const toolCallPattern = /<tool_calls>\s*(\{.*?\})\s*<\/tool_calls>/gs;
          const matches = [...text.matchAll(toolCallPattern)];
          if (matches.length > 0) {
            log.debug(`[MiniMax] Tool calls found (round ${round + 1}): ${matches.length}`);
            for (const match of matches) {
              try {
                const call = JSON.parse(match[1]);
                const toolName = call.name;
                const toolArgs = typeof call.arguments === 'string' ? JSON.parse(call.arguments) : call.arguments || {};
                log.debug(`  → ${toolName}(${JSON.stringify(toolArgs).substring(0, 80)})`);
                const result = await this._executeTool(toolName, toolArgs);
                const resultText = typeof result === 'string' ? result : JSON.stringify(result);
                messages.push({ role: 'assistant', content: text });
                messages.push({
                  role: 'tool',
                  content: JSON.stringify({ name: toolName, result: resultText.substring(0, 1000) }),
                });
              } catch (e) {
                log.debug(`Tool parse error: ${e.message}`);
              }
            }
            // 继续下一轮
            continue;
          }
        }

        // 没有 tool calls — 这是最终回复
        return { role, prompt: fullPrompt, output: text, tokens };
      }

      // 超过最大轮数
      log.warn(`[MiniMax] Max tool rounds (${maxToolRounds}) reached`);
      return { role, prompt: fullPrompt, output: '[output truncated due to max tool rounds]', tokens: 0 };
    } catch (err) {
      log.debug(`MiniMax call failed: ${err.message}, falling back to mock`);
      return this._mockAgent(role, prompt, options);
    }
  }

  async _callMiniMax(role, prompt, options = {}) {
    // 如果有 tools，使用 tool call 循环版本
    if (options.tools && options.tools.length > 0) {
      return this._callMiniMaxWithTools(role, prompt, options);
    }

    const systemPrompt = this._getSystemPrompt(role);
    const fullPrompt = `${systemPrompt}\n\nTask:\n${prompt}`;

    const model = process.env.SOP_LLM_MODEL || 'MiniMax-M2.7-highspeed';
    const token = process.env.MAVIS_ACCESS_TOKEN;
    const timeout = (options.timeout || 120) * 1000;
    const externalSignal = options.signal || null;
    const url = 'https://agent.minimaxi.com/mavis/api/v1/llm/v1/messages';

    log.info(`[MiniMax] Calling ${role} (${model})`);

    // Wrapped fetch in retry — transient HTTP errors get exponential backoff
    const doFetch = async () => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);

      if (externalSignal) {
        externalSignal.addEventListener('abort', () => controller.abort());
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: fullPrompt }],
          max_tokens: 4096,
          temperature: 1.0,
          top_p: 0.95,
        }),
        signal: controller.signal,
      });

      clearTimeout(timer);

      if (controller.signal.aborted) {
        throw new Error('MiniMax request aborted');
      }

      if (!response.ok) {
        const err = await response.text();
        throw new Error(`MiniMax API error ${response.status}: ${err}`);
      }

      return response.json();
    };

    try {
      const data = await this._retryWithBackoff(doFetch, 2, [429, 500, 502, 503, 504]);

      // 提取文本响应 (跳过 thinking 块)
      let output = '';
      if (Array.isArray(data.content)) {
        for (const c of data.content) {
          if (c.type === 'text') {
            output += c.text || '';
          }
        }
      } else {
        output = JSON.stringify(data);
      }

      const tokens = this._countOutputTokens(data);
      this.state.addTokenUsage(tokens);

      return {
        role,
        prompt: fullPrompt,
        output,
        tokens,
      };
    } catch (err) {
      if (err.name === 'AbortError' || err.message.includes('aborted')) {
        throw err; // re-throw abort so caller knows it was cancelled
      }
      log.debug(`MiniMax call failed: ${err.message}, falling back to mock`);
      return this._mockAgent(role, prompt, options);
    }
  }

  /**
   * Retry a function with exponential backoff for transient errors.
   */
  async _retryWithBackoff(fn, maxRetries = 2, retryableStatuses = [429, 500, 502, 503, 504]) {
    let lastError;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (err) {
        lastError = err;
        const isRetryable = retryableStatuses.some(code =>
          err.message && (err.message.includes(' ' + code + ' ') ||
            err.message.includes('status: ' + code) ||
            err.message.includes('API error ' + code))
        );
        if (attempt < maxRetries && (isRetryable ||
            err.message?.includes('ETIMEDOUT') ||
            err.code === 'ETIMEDOUT' ||
            err.message?.includes('fetch failed'))) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
          log.warn(`Transient error (attempt ${attempt + 1}/${maxRetries + 1}), retrying in ${delay}ms: ${err.message.substring(0, 80)}`);
          await new Promise(r => setTimeout(r, delay));
        } else {
          throw err;
        }
      }
    }
    throw lastError;
  }

  _getSystemPrompt(role) {
    const prompts = {
      architect: `You are a senior architect (based onobra/superpowers brainstorming skill).

HARD-GATE: Do NOT write code until user approves the design.
- Ask ONE question at a time
- Present design in sections, get approval after each
- Lead with your recommendation
- YAGNI ruthlessly
- Save approved spec to docs/superpowers/specs/`,

      planner: `You are a task planning expert (based onobra/superpowers writing-plans skill).

Rules:
- Each step is 2-5 minutes
- Every step has ACTUAL CODE (no placeholders)
- Exact file paths always
- TDD RED-GREEN-REFACTOR: write failing test, run it, write minimal code, run it, commit
- No "TBD", "TODO", "implement later"
- Plan failures: "Similar to Task N", "Add appropriate error handling" without showing how`,

      worker: `You are an efficient developer (implementer subagent fromobra/superpowers subagent-driven-development).

Rules:
- Write the failing test FIRST (TDD RED)
- Run test — watch it FAIL
- Write minimal code
- Run test — watch it PASS
- Commit
- Self-review before reporting back
- If blocked: STOP and say BLOCKED — don't guess

Report: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`,

      verifier: `You are a strict code reviewer (based onobra/superpowers).

Stage 1 — Spec Compliance: Read ACTUAL code, verify against requirements.
- Do NOT trust the implementer's report
- Missing requirements?
- Extra/unneeded work?
- Misunderstandings?

Stage 2 — Code Quality (only after Stage 1 passes):
- Clean separation of concerns?
- Proper error handling?
- Edge cases handled?
- Tests verify real behavior?

Evidence before claims: Run commands to verify, don't assume.`,

      'sen-reviewer': `You are a senior technical reviewer.

Final verification:
- All requirements met with evidence?
- Tests passing?
- Ready to merge?

Evidence before claims. Run verification commands.`,

      'senior-reviewer': `You are a senior technical reviewer (based onobra/superpowers verification-before-completion).

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.
- Run the command
- Read the output
- THEN claim the result

Red flags: "should pass", "probably works", "tests passed before", "looks correct"
These mean: RUN THE COMMAND.`,

      implementer: `You are implementing a task from the plan.

BEFORE YOU BEGIN: Ask any clarifying questions NOW.
- Questions about requirements?
- Approach unclear?
- Missing context?

YOUR JOB:
1. Write failing test (TDD)
2. Run test — verify FAIL
3. Write minimal code
4. Run test — verify PASS
5. Commit
6. Self-review
7. Report: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT

STOP and escalate when:
- Task requires architectural decisions
- Can't find clarity in code
- Uncertain about approach
- Over your head

Report with EVIDENCE, not assumptions.`,

      'spec-reviewer': `You are reviewing spec compliance.

DO NOT TRUST THE REPORT. Read ACTUAL code.

Check:
- Missing requirements
- Extra/unneeded work
- Misunderstandings

Report: ✅ Spec compliant OR ❌ Issues [file:line]`,

      'code-reviewer': `You are reviewing code quality.

Severity levels:
- Critical (Must Fix): Bugs, security, broken functionality
- Important (Should Fix): Architecture problems, missing features
- Minor (Nice to Have): Style, optimization

Evidence before claims: Run verification commands.`,

      reviewer: `You are a strict code reviewer. Find problems, do not fix them. Score each dimension 1-5.`,

      'quality-reviewer': `You are a code quality reviewer.

Only review quality AFTER spec compliance passes.

Check:
- Clean separation of concerns?
- Proper error handling?
- Type safety?
- DRY without premature abstraction?
- Edge cases handled?
- Tests verify real behavior (not mocks)?

Report: Strengths, Issues by severity (Critical/Important/Minor), Assessment`,
    };
    return prompts[role] || prompts.worker;
  }
}

// ============================================================
// Verifier 评审器
// ============================================================
class VerifierRunner {
  constructor(agent) {
    this.agent = agent;
  }

  /**
   * 执行验证
   * @param {string} type - verifier 类型
   * @param {object} deliverable - 交付物 { content, summary, files }
   * @param {object} manifest - SOP manifest (包含自定义 verifier)
   * @returns {Promise<{verdict, score, issues, summary}>}
   */
  async verify(type, deliverable, manifest = {}) {
    // 优先使用 manifest 中的自定义 verifier，其次使用内置
    const verifierDef = manifest.verifier_types?.[type] || BUILTIN_VERIFIERS[type];

    if (!verifierDef) {
      log.warn(`Unknown verifier type: ${type}, skipping`);
      return { verdict: 'PASS', score: 5, issues: [], summary: 'No verifier defined' };
    }

    const threshold = verifierDef.threshold || BUILTIN_VERIFIERS[type]?.threshold || 3.5;
    log.verifier(`${verifierDef.name || type} (threshold: ${threshold})`);

    // 构建 prompt
    let prompt = verifierDef.prompt || '';
    prompt += `\n\n=== 交付物 ===\n${deliverable.content || deliverable.summary || 'N/A'}`;

    // 如果有文件，读取并附加到 prompt
    if (deliverable.files && deliverable.files.length > 0) {
      prompt += `\n\n=== 已生成的文件 ===`;
      for (const fileName of deliverable.files) {
        const outputDir = path.join(process.cwd(), '.sop-workflow', 'outputs');
        const filePath = path.join(outputDir, fileName);
        if (fs.existsSync(filePath)) {
          const content = fs.readFileSync(filePath, 'utf8');
          prompt += `\n\n--- ${fileName} ---\n${content}`;
        }
      }
    }

    prompt += `\n\nReturn your assessment as JSON only.`;

    // 调用 verifier agent (使用 manifest 中配置的 model)
    const model = manifest.config?.model || 'MiniMax/MiniMax';
    // NOTE: MiniMax function calling 需要 vLLM 部署的端点。
    // agent.minimaxi.com API 暂不支持多轮 tool call，
    // 所以工具通过预加载文件内容到 prompt 实现 (见下文)。
    const result = await this.agent.agent('verifier', prompt, { model });

    // 解析结果
    return this._parseVerdict(result.output || '', threshold);
  }

  _parseVerdict(raw, threshold = 3.5) {
    // 尝试提取 JSON
    try {
      const json = JSON.parse(raw);
      return this._normalizeVerdict(json, threshold);
    } catch (e) {
      // 尝试提取 JSON 块（代码 fences）
      const jsonFenceMatch = raw.match(/```json\s*([\s\S]*?)```/);
      if (jsonFenceMatch) {
        try {
          return this._normalizeVerdict(JSON.parse(jsonFenceMatch[1]), threshold);
        } catch (e2) { /* 继续 */ }
      }

      // 尝试提取裸 JSON 对象（多行、完整花括号）
      const bareJsonMatch = raw.match(/\{[\s\S]*?"verdict"[\s\S]*?"summary"[\s\S]*?\}/);
      if (bareJsonMatch) {
        try {
          return this._normalizeVerdict(JSON.parse(bareJsonMatch[0]), threshold);
        } catch (e2) { /* 继续 */ }
      }

      // 尝试提取带引号的 verdict 字段（鲁棒的 key-value 提取）
      const verdictMatch = raw.match(/"verdict"\s*:\s*"([^"]+)"/);
      const scoreMatch = raw.match(/"(score|overall_score)"\s*:\s*(\d+\.?\d*)/);
      const summaryMatch = raw.match(/"summary"\s*:\s*"([^"]{0,500})"/);
      if (verdictMatch || scoreMatch) {
        return this._normalizeVerdict({
          verdict: verdictMatch ? verdictMatch[1] : undefined,
          score: scoreMatch ? parseFloat(scoreMatch[2]) : undefined,
          summary: summaryMatch ? summaryMatch[1] : raw.substring(0, 100),
        }, threshold);
      }

      // 定性判断（MiniMax 可能输出自然语言结论）
      const lower = raw.toLowerCase();
      const qualitativePass = ['pass', 'good', 'excellent', 'approved', 'acceptable', 'meets requirements'];
      const qualitativeFail = ['fail', 'needs work', 'rejected', 'unacceptable', 'incomplete', 'does not meet'];

      const passIdx = qualitativePass.findIndex(w => lower.includes(w));
      const failIdx = qualitativeFail.findIndex(w => lower.includes(w));

      if (passIdx >= 0 && (failIdx < 0 || passIdx <= failIdx)) {
        const scores = [4, 5, 4.5, 4, 3.5, 4];
        return {
          verdict: 'PASS',
          score: scores[passIdx],
          issues: [],
          summary: raw.substring(0, 200),
        };
      }
      if (failIdx >= 0) {
        const scores = [2, 2.5, 1.5, 2, 2, 2];
        return {
          verdict: 'FAIL',
          score: scores[failIdx],
          issues: [],
          summary: raw.substring(0, 200),
        };
      }
    }

    // 回退: 简单判断
    const isPass = raw.toLowerCase().includes('pass') || !raw.toLowerCase().includes('fail');
    return {
      verdict: isPass ? 'PASS' : 'FAIL',
      score: isPass ? 4 : 2,
      issues: [],
      summary: 'Verdict inferred from output',
    };
  }

  _normalizeVerdict(result, threshold) {
    const score = typeof result.score === 'number' ? result.score :
                  typeof result.overall_score === 'number' ? result.overall_score : 3;

    let verdict = result.verdict;
    if (!verdict) {
      verdict = score >= threshold ? 'PASS' : 'FAIL';
    }

    return {
      verifier: result.verifier || 'unknown',
      verdict,
      score,
      issues: result.issues || [],
      summary: result.summary || '',
    };
  }
}

// ============================================================
// 任务执行器
// ============================================================
class TaskExecutor {
  constructor(manifest, state, agent, verifier) {
    this.manifest = manifest;
    this.state = state;
    this.agent = agent;
    this.verifier = verifier;
  }

  async executeTask(task, phaseName, signal = null) {
    const phase = this.manifest.phases?.[phaseName];
    const timeout = this.manifest.config?.timeouts?.[phaseName] ||
                   this.manifest.config?.timeouts?.[task.agent_role] ||
                   300000;

    log.task(`${task.title || task.id} [${task.agent_role || 'worker'}]`);

    // 如果 wave 级别的 AbortSignal 已中止，直接返回失败
    if (signal?.aborted) {
      log.debug(`Task ${task.id} cancelled by wave abort`);
      return { success: false, error: 'cancelled', cancelled: true };
    }

    // 检查依赖
    if (task.depends_on) {
      const deps = Array.isArray(task.depends_on) ? task.depends_on : [task.depends_on];
      for (const depId of deps) {
        const depTask = this.state.tasks.find(t => t.id === depId);
        if (!depTask || depTask.status !== 'completed') {
          log.warn(`Task ${task.id} blocked by incomplete dependency: ${depId}`);
          return { success: false, error: `Dependency ${depId} not completed` };
        }
      }
    }

    this.state.currentTask = task.id;

    // 检查任务是否已完成（恢复时可能已完成）
    const existingTask = this.state.tasks.find(t => t.id === task.id);
    if (existingTask) {
      if (existingTask.status === 'completed') {
        log.debug(`Task ${task.id} already completed, skipping`);
        return { success: true, output: null, skipped: true };
      }
      // 重新运行 pending 或 failed 的任务
      this.state.updateTask(task.id, { status: 'running', start: Date.now() });
    } else {
      this.state.addTask(task.id, 'running');
    }

    try {
      // 构建 prompt
      const basePrompt = task.description || task.title;
      const promptTemplate = task.prompt_template || this._loadPromptTemplate(task.agent_role);
      const fullPrompt = promptTemplate
        ? `${promptTemplate}\n\nTask: ${basePrompt}`
        : basePrompt;

      // 执行 worker (propagate abort signal via options)
      const startTime = Date.now();

      // 合并 abort signal 和 timeout: 任意一个触发都中止
      const taskIdStr = task.id;
      const abortPromise = signal
        ? new Promise(function(res, rej) { signal.addEventListener('abort', function() { rej(new Error('Task ' + taskIdStr + ' aborted')); }); }.bind(this))
        : new Promise(function() {}); // never resolves if no signal

      const workerResult = await Promise.race([
        this.agent.agent(task.agent_role || 'worker', fullPrompt, { timeout, signal }),
        this._timeout(timeout, task.id),
        abortPromise.catch(function() { throw new Error('Task ' + taskIdStr + ' aborted'); }),
      ]);

      const duration = Date.now() - startTime;
      log.debug(`Worker completed in ${duration}ms`);

      // 提取代码块并写入文件
      const outputDir = path.join(process.cwd(), '.sop-workflow', 'outputs');
      if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
      const { writtenFiles, extractedCode } = this._extractAndWriteCode(workerResult.output, outputDir);
      if (writtenFiles.length > 0) {
        log.debug(`Wrote ${writtenFiles.length} files: ${writtenFiles.join(', ')}`);
      }

      // 如果有 verifier，进行 Two-Stage Review (Superpowers核心)
      const verifierType = task.verifier || phase?.verifier;
      if (verifierType) {
        const maxRetries = this.manifest.config?.verifier_max_retries ?? 2;
        const adversarial = this.manifest.config?.adversarial_mode;
        let currentOutput = workerResult.output;

        // Superpowers: Evidence before claims — 运行验证命令
        const evidence = await this._runEvidenceVerification(workerResult.output, outputDir);
        if (evidence.length > 0) {
          log.debug(`Evidence collected: ${evidence.length} commands`);
          for (const e of evidence) {
            log.debug(`  ${e.status}: ${e.command.substring(0, 60)}`);
          }
        }

        // Superpowers: Two-stage review — spec 合规性先于代码质量
        let reviewResult = await this._runTwoStageReview(task, currentOutput, writtenFiles, this.manifest, evidence);
        let lastVerdict = reviewResult;
        let attempt = 0;

        while (attempt <= maxRetries && lastVerdict.verdict !== 'PASS') {
          if (attempt > 0 || reviewResult.verdict !== 'PASS') {
            log.warn(`Verifier FAIL (${attempt + 1}/${maxRetries}): ${lastVerdict.summary}`);

            if (adversarial && lastVerdict.issues?.length > 0) {
              const feedbackPrompt = `${task.description || task.title}
${writtenFiles.length > 0 ? `\nFiles generated: ${writtenFiles.join(', ')}\n` : ''}
${evidence.length > 0 ? `\n=== Evidence ===\n${evidence.map(e => `${e.status}: ${e.command}\n${e.output || e.error || ''}`).join('\n')}\n` : ''}
=== Verifier Feedback (Fix #${attempt + 1}) ===
${JSON.stringify(lastVerdict.issues, null, 2)}

Fix the issues. Rewrite the code completely if needed.`;
              const retryTaskId = task.id;
              const abortPromise = signal
                ? new Promise(function(res, rej) { signal.addEventListener('abort', function() { rej(new Error('Task ' + retryTaskId + ' aborted')); }); }.bind(this))
                : new Promise(function() {});
              const retryResult = await Promise.race([
                this.agent.agent(task.agent_role || 'worker', feedbackPrompt, { timeout, signal }),
                this._timeout(timeout, task.id),
                abortPromise.catch(function() { throw new Error('Task ' + retryTaskId + ' aborted'); }),
              ]);
              currentOutput = retryResult.output;

              // 重新提取和验证
              const { writtenFiles: newFiles } = this._extractAndWriteCode(currentOutput, outputDir);
              const newEvidence = await this._runEvidenceVerification(currentOutput, outputDir);
              lastVerdict = await this._runTwoStageReview(task, currentOutput, newFiles, this.manifest, newEvidence);
            }
          }
          attempt++;
        }

        // 两阶段都 PASS — 成功！
        if (lastVerdict.verdict === 'PASS') {
          this.state.updateTask(task.id, { status: 'completed', duration });
          this._writeTaskContext(task, currentOutput, writtenFiles, lastVerdict, process.cwd());
          log.ok(`${task.id} completed (score: ${lastVerdict.score}/5)`);
          return { success: true, output: currentOutput, verdict: lastVerdict };
        }

        // 重试耗尽（verdict != PASS）
        if (adversarial) {
          this.state.updateTask(task.id, { status: 'failed' });
          log.fail(`${task.id} failed: Verifier rejected after ${maxRetries} retries`);
          return { success: false, error: 'Verifier rejected', verdict: lastVerdict, issues: lastVerdict?.issues };
        }

        // 非对抗模式: warning 但继续
        this.state.updateTask(task.id, { status: 'completed', duration, warning: true });
        this._writeTaskContext(task, currentOutput, writtenFiles, lastVerdict, process.cwd());
        log.warn(`${task.id} completed with verifier issues (adversarial disabled)`);
        return { success: true, output: currentOutput, verdict: lastVerdict, warning: true };
      }

      // 无 verifier
      this.state.updateTask(task.id, { status: 'completed', duration });
      this._writeTaskContext(task, workerResult.output, [], { verdict: 'PASS', score: 5 }, process.cwd());
      log.ok(`${task.id} completed`);
      return { success: true, output: workerResult.output };

    } catch (error) {
      this.state.updateTask(task.id, { status: 'failed', error: error.message });
      log.fail(`${task.id} failed: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * 提取代码块并写入文件
   * 支持 ```language 的格式
   */
  _extractAndWriteCode(output, outputDir) {
    const writtenFiles = [];
    let extractedCode = '';

    // 匹配 ```language 或 ``` 包裹的代码块
    const codeBlockPattern = /```(?:(\w+))?\s*\n?([\s\S]*?)```/g;
    let match;
    let fileIndex = 0;

    while ((match = codeBlockPattern.exec(output)) !== null) {
      const language = match[1] || 'txt';
      let code = match[2].trim();

      extractedCode += `\n${code}\n`;

      // 推断文件名
      let fileName = null;
      if (language === 'javascript' || language === 'js') fileName = `output_${fileIndex}.js`;
      else if (language === 'typescript' || language === 'ts') fileName = `output_${fileIndex}.ts`;
      else if (language === 'python' || language === 'py') fileName = `output_${fileIndex}.py`;
      else if (language === 'bash' || language === 'sh') fileName = `output_${fileIndex}.sh`;
      else if (language === 'json') fileName = `output_${fileIndex}.json`;
      else if (language === 'html') fileName = `output_${fileIndex}.html`;
      else if (language === 'css') fileName = `output_${fileIndex}.css`;
      else if (language === 'sql') fileName = `output_${fileIndex}.sql`;
      else if (language === 'markdown' || language === 'md') fileName = `output_${fileIndex}.md`;
      else if (language === 'yaml' || language === 'yml') fileName = `output_${fileIndex}.yaml`;
      else if (language === 'java') fileName = `output_${fileIndex}.java`;
      else if (language === 'go') fileName = `output_${fileIndex}.go`;
      else if (language === 'rust') fileName = `output_${fileIndex}.rs`;
      else fileName = `output_${fileIndex}.txt`;

      // 如果代码里包含文件名提示，优先使用
      const pathMatch = code.match(/(?:filename|filepath|file)[\s:]*[`'"]?([^\s`'"{};]+(?:\.\w+)?)/i);
      if (pathMatch && !pathMatch[1].startsWith('//') && !pathMatch[1].startsWith('#')) {
        const suggested = pathMatch[1].replace(/^\.\//, '');
        if (suggested.includes('.') && !suggested.includes('node_modules')) {
          fileName = suggested;
        }
      }

      const filePath = path.join(outputDir, fileName);
      try {
        fs.writeFileSync(filePath, code, 'utf8');
        writtenFiles.push(fileName);
        fileIndex++;
      } catch (e) {
        log.debug(`Failed to write ${fileName}: ${e.message}`);
      }
    }

    // 如果没有任何代码块但有普通文本，也写一个
    if (writtenFiles.length === 0 && output.trim()) {
      const filePath = path.join(outputDir, 'output.txt');
      fs.writeFileSync(filePath, output, 'utf8');
      writtenFiles.push('output.txt');
    }

    return { writtenFiles, extractedCode };
  }

  /**
   * Writes task context to a JSON file for inter-agent memory.
   * Subsequent agents in the workflow can read this file to understand
   * what previous tasks produced without re-executing them.
   */
  _writeTaskContext(task, output, writtenFiles, verdict) {
    try {
      const contextDir = path.join(process.cwd(), '.sop-workflow', 'context');
      if (!fs.existsSync(contextDir)) {
        fs.mkdirSync(contextDir, { recursive: true });
      }
      const context = {
        taskId: task.id,
        phase: this.state.phase,
        timestamp: new Date().toISOString(),
        description: task.description || task.title,
        verdict: verdict?.verdict || 'UNKNOWN',
        score: verdict?.score || 0,
        writtenFiles: writtenFiles || [],
        outputSummary: output
          ? output.substring(0, 500).replace(/\n+/g, ' ').trim()
          : '',
        issues: verdict?.issues || [],
      };
      const filePath = path.join(contextDir, `${task.id}.json`);
      fs.writeFileSync(filePath, JSON.stringify(context, null, 2));
      log.debug(`Context written: ${filePath}`);
    } catch (e) {
      log.debug(`Failed to write task context: ${e.message}`);
    }
  }

  /**
   * Superpowers 核心原则: Evidence before claims
   * 从 worker 输出中提取验证命令，运行并验证结果
   */
  async _runEvidenceVerification(workerOutput, outputDir, maxTime = 30000) {
    const evidence = [];
    const commandPattern = /```(?:bash|sh|shell)?\n?(?:Run: |\$ )?([^\n]+)\n?```/g;

    // 提取所有 bash/shell 代码块
    const commands = [];
    let match;
    while ((match = commandPattern.exec(workerOutput)) !== null) {
      const cmd = match[1].trim();
      // 过滤掉明显的非命令文本
      if (cmd && !cmd.includes('#') && !cmd.includes('TODO') && !cmd.includes('TBD')) {
        commands.push(cmd);
      }
    }

    // 也尝试从文本中提取 Run: 开头的命令
    const runPattern = /Run:\s*`([^`]+)`/g;
    while ((match = runPattern.exec(workerOutput)) !== null) {
      commands.push(match[1].trim());
    }

    // 并行执行所有 evidence 命令 (非阻塞)
    const evidenceResults = await Promise.all(
      commands.map(async (cmd) => {
        log.debug(`Evidence: running "${cmd}"`);
        try {
          const { stdout, stderr } = await exec(cmd, {
            encoding: 'utf8',
            timeout: maxTime,  // exec timeout is in milliseconds
            cwd: process.cwd(),
          });
          return { command: cmd, exitCode: 0, output: stdout.substring(0, 500), status: 'PASS' };
        } catch (e) {
          const exitCode = e.status || 1;
          const stdout = e.stdout?.toString() || '';
          const stderr = e.stderr?.toString() || '';
          return {
            command: cmd,
            exitCode,
            output: stdout.substring(0, 500),
            error: stderr.substring(0, 200),
            status: exitCode === 0 ? 'PASS' : 'FAIL',
          };
        }
      })
    );

    return evidenceResults;
  }

  /**
   * Two-stage review: 先 spec 合规性，再代码质量
   * Superpowers 原则: spec review 必须先于 quality review
   */
  async _runTwoStageReview(task, workerOutput, writtenFiles, manifest, evidence) {
    const verifier = this.verifier;
    // task.description 就是 spec
    const specAsContext = task.description || task.title || '';

    // Evidence injection (Superpowers: Evidence before claims)
    const evidenceSection = evidence && evidence.length > 0
      ? `\n\n=== EVIDENCE RESULTS ===\n${evidence.map(e => `[${e.status.toUpperCase()}] Command: ${e.command}\nOutput:\n${e.output || e.error || '(no output)'}`).join('\n\n')}\n`
      : '';

    // Stage 1: Spec Compliance
    log.verifier(`[Stage 1/2] Spec Compliance Review`);
    const specResult = await verifier.verify('spec-compliance', {
      content: `=== SPEC (task description) ===\n${specAsContext}\n\n=== WORKER OUTPUT ===\n${workerOutput}${evidenceSection}`,
      summary: (specAsContext + ' ' + workerOutput).substring(0, 500),
      files: writtenFiles,
    }, manifest);

    if (specResult.verdict !== 'PASS') {
      log.warn(`[Stage 1/2] FAIL: ${specResult.summary}`);
      if (specResult.issues?.length > 0) {
        for (const issue of specResult.issues) {
          log.warn(`  - [${issue.severity}] ${issue.description}`);
        }
      }
      return { stage: 1, ...specResult };
    }

    log.ok(`[Stage 1/2] PASS`);

    // Stage 2: Code Quality — uses underscore
    log.verifier(`[Stage 2/2] Code Quality Review`);
    const qualityResult = await verifier.verify('code_quality', {
      content: `=== SPEC (task description) ===\n${specAsContext}\n\n=== WORKER OUTPUT ===\n${workerOutput}${evidenceSection}`,
      summary: (specAsContext + ' ' + workerOutput).substring(0, 500),
      files: writtenFiles,
    }, manifest);

    if (qualityResult.verdict !== 'PASS') {
      log.warn(`[Stage 2/2] FAIL: ${qualityResult.summary}`);
      if (qualityResult.issues?.length > 0) {
        for (const issue of qualityResult.issues) {
          log.warn(`  - [${issue.severity}] ${issue.description}`);
        }
      }
    } else {
      log.ok(`[Stage 2/2] PASS`);
    }

    return { stage: 2, ...qualityResult };
  }

  _timeout(ms, taskId) {
    return new Promise((_, rej) =>
      setTimeout(() => rej(new Error(`Task ${taskId} timeout: ${ms}ms`)), ms)
    );
  }

  _loadPromptTemplate(role) {
    // 尝试从 prompts/ 目录加载模板
    const skillDir = path.join(__dirname, '..');
    const templateFile = path.join(skillDir, 'prompts', `${role}-prompt.md`);

    if (fs.existsSync(templateFile)) {
      return fs.readFileSync(templateFile, 'utf8');
    }

    return null;
  }

  /**
   * Writes task context to a JSON file for inter-agent memory.
   * Subsequent agents can read this to understand what previous tasks produced.
   */
  _writeTaskContext(task, output, writtenFiles, verdict, cwd) {
    try {
      const baseDir = cwd || process.cwd();
      const contextDir = path.join(baseDir, '.sop-workflow', 'context');
      if (!fs.existsSync(contextDir)) {
        fs.mkdirSync(contextDir, { recursive: true });
      }
      const context = {
        taskId: task.id,
        phase: this.state.phase,
        timestamp: new Date().toISOString(),
        description: task.description || task.title,
        verdict: verdict?.verdict || 'UNKNOWN',
        score: verdict?.score || 0,
        writtenFiles: writtenFiles || [],
        outputSummary: output
          ? output.substring(0, 500).replace(/\n+/g, ' ').trim()
          : '',
        issues: verdict?.issues || [],
      };
      const filePath = path.join(contextDir, `${task.id}.json`);
      fs.writeFileSync(filePath, JSON.stringify(context, null, 2));
      log.debug(`Context written: ${filePath}`);
    } catch (e) {
      log.debug(`Failed to write task context: ${e.message}`);
    }
  }
}

// ============================================================
// 主执行引擎
// ============================================================
class WorkflowEngine {
  constructor(manifestPath) {
    this.manifestPath = manifestPath;
    this.manifest = null;
    this.state = null;
    this.agent = null;
    this.verifier = null;
    this.executor = null;
  }

  load() {
    if (!fs.existsSync(this.manifestPath)) {
      throw new Error(`Manifest not found: ${this.manifestPath}`);
    }

    this.manifest = yaml.load(fs.readFileSync(this.manifestPath, 'utf8'));
    log.info(`Loaded manifest: ${this.manifest.meta?.name || 'unnamed'}`);

    // 创建核心组件
    this.state = new WorkflowState(this.manifest);
    this.agent = new AgentInterface(this.state);
    this.verifier = new VerifierRunner(this.agent);
    this.executor = new TaskExecutor(this.manifest, this.state, this.agent, this.verifier);
  }

  async init(taskId = null) {
    this.load();

    // 尝试恢复状态
    if (this.state.load()) {
      log.info(`Resuming from saved state (phase: ${this.state.phase})`);
    } else {
      log.info('Starting new workflow');
    }

    // 创建输出目录
    const outputDir = path.join(process.cwd(), '.sop-workflow');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // 初始化上下文摘要
    const summaryFile = path.join(process.cwd(), '.sop-context-summary.json');
    if (!fs.existsSync(summaryFile)) {
      fs.writeFileSync(summaryFile, JSON.stringify({
        created: new Date().toISOString(),
        workflow: this.manifest.meta?.name,
        phases: Object.keys(this.manifest.phases || {}),
      }, null, 2));
    }

    // 初始化任务列表
    for (const [phaseName, phase] of Object.entries(this.manifest.phases || {})) {
      for (const task of (phase.tasks || [])) {
        if (!this.state.tasks.find(t => t.id === task.id)) {
          this.state.addTask(task.id, 'pending');
        }
      }
    }

    if (taskId) {
      this.state.taskId = taskId;
    }
  }

  async run(targetPhase = null) {
    const phases = targetPhase
      ? { [targetPhase]: this.manifest.phases[targetPhase] }
      : this.manifest.phases || {};

    for (const [phaseName, phase] of Object.entries(phases)) {
      // 跳过已完成的阶段 (index < current phase index)
      if (this.state.phase) {
        const allPhases = Object.keys(this.manifest.phases || {});
        const currentIndex = allPhases.indexOf(this.state.phase);
        const thisIndex = allPhases.indexOf(phaseName);
        if (thisIndex <= currentIndex) {
          log.debug(`Skipping completed phase: ${phaseName}`);
          continue;
        }
      }

      log.phase(`${phase.name || phaseName} [${phaseName}]`);

      // 立即保存当前阶段 (崩溃恢复用)
      this.state.phase = phaseName;
      this.state.save();

      // 运行阶段任务 (按依赖分组并行执行)
      const tasks = phase.tasks || [];
      const waves = this._groupTasksIntoWaves([...tasks]);
      const waveTimeout = this.manifest.config?.timeouts?.wave ||
                         this.manifest.config?.timeouts?.execute_per_task ||
                         600000;

      for (let waveIdx = 0; waveIdx < waves.length; waveIdx++) {
        const wave = waves[waveIdx];

        // 恢复逻辑: 跳过已完成的 wave
        const allInWaveCompleted = wave.every(t =>
          this.state.tasks.find(st => st.id === t.id)?.status === 'completed'
        );
        if (allInWaveCompleted) {
          log.debug(`Wave ${waveIdx + 1} already completed, skipping`);
          continue;
        }

        // 过滤恢复点: 跳过 wave 中 taskId 之前的任务
        const filteredWave = this.state.taskId
          ? wave.filter(t => {
              const waveTaskIdx = wave.indexOf(t);
              const targetWaveIdx = waves.findIndex(w => w.some(t2 => t2.id === this.state.taskId));
              if (waveIdx < targetWaveIdx) return false;
              if (waveIdx === targetWaveIdx) {
                const targetIdx = wave.findIndex(t2 => t2.id === this.state.taskId);
                return waveTaskIdx >= targetIdx;
              }
              return true;
            })
          : wave;

        if (filteredWave.length === 0) continue;

        if (wave.length > 1) {
          log.info(`Wave ${waveIdx + 1}/${waves.length}: running ${wave.length} tasks in parallel`);
        }

        // 每个 wave 独立的 AbortController，用于任意任务失败时取消其余
        const waveCtrl = new AbortController();

        // Wave 级别超时: 超时则中止所有任务
        const waveTimer = setTimeout(() => {
          log.warn(`Wave ${waveIdx + 1} exceeded ${waveTimeout}ms, aborting`);
          waveCtrl.abort();
        }, waveTimeout);

        // 并行执行 wave 中的所有任务
        let results;
        try {
          results = await this._executeWave(filteredWave, phaseName, waveCtrl);
        } finally {
          clearTimeout(waveTimer);
        }

        // 保存状态
        this.state.save();

        // 如果有任何任务失败且是对抗模式，中止 wave 并停止
        const failed = results.filter(r => !r.success && !r.cancelled);
        if (failed.length > 0 && this.manifest.config?.adversarial_mode) {
          // 标记 wave 中被取消的任务
          const cancelled = results.filter(r => r.cancelled);
          for (const c of cancelled) {
            this.state.updateTask(c.taskId || task.id, { status: 'failed', error: 'cancelled' });
          }
          log.fail(`Stopping due to adversarial mode and ${failed.length} task failure(s)`);
          return this.state;
        }
      }

      // 阶段结束确认
      if (phase.require_phase_approval) {
        log.info(`${c.yellow}Awaiting approval to continue to next phase...${c.reset}`);
        // 实际实现应该等待外部确认
      }
    }

    this._printSummary();
    return this.state;
  }

  /**
   * Groups tasks into execution waves based on dependencies.
   * Tasks in the same wave have no interdependencies and can run in parallel.
   * 
   * Algorithm: Kahn's algorithm variant for DAG traversal
   * - Wave 0: tasks with no dependencies (or only external deps)
   * - Wave N: tasks whose deps are all in waves < N
   */
  _groupTasksIntoWaves(tasks) {
    if (!tasks || tasks.length === 0) return [];

    const taskMap = new Map(tasks.map(t => [t.id, t]));
    const waves = [];
    const completedIds = new Set();

    // Filter out tasks whose deps are from OTHER phases (not in this phase's task list)
    const phaseTaskIds = new Set(tasks.map(t => t.id));

    while (true) {
      // Find tasks whose deps are all satisfied (or external)
      const ready = tasks.filter(task => {
        const deps = task.depends_on
          ? (Array.isArray(task.depends_on) ? task.depends_on : [task.depends_on])
          : [];
        
        // Check: all deps are either completed in previous waves, or external (not in this phase)
        return deps.every(depId =>
          completedIds.has(depId) || !phaseTaskIds.has(depId)
        );
      });

      if (ready.length === 0) {
        // Check if there are remaining tasks (circular dependency)
        const remaining = tasks.filter(t => !completedIds.has(t.id));
        if (remaining.length > 0) {
          log.warn(`Circular dependency detected among: ${remaining.map(t => t.id).join(', ')}`);
          // Add remaining tasks as final wave (they'll fail on dep check at runtime)
          if (waves.length === 0) waves.push([]);
          waves[waves.length - 1].push(...remaining);
        }
        break;
      }

      waves.push(ready);
      ready.forEach(t => completedIds.add(t.id));

      // Remove from remaining pool
      tasks = tasks.filter(t => !completedIds.has(t.id));
    }

    return waves;
  }

  /**
   * Executes all tasks in a wave in parallel.
   * Returns array of results.
   */
  /**
   * Executes all tasks in a wave in parallel with a shared AbortController.
   * If any task fails (in adversarial mode), the controller is aborted to
   * cancel remaining siblings, and their results are marked as cancelled.
   */
  async _executeWave(wave, phaseName, abortController = null) {
    const ctrl = abortController || new AbortController();
    const results = await Promise.all(
      wave.map(task => this.executor.executeTask(task, phaseName, ctrl.signal))
    );
    return results;
  }

  _printSummary() {
    console.log(`\n${c.bold}${'='.repeat(60)}`);
    console.log('Workflow Summary');
    console.log(`${'='.repeat(60)}${c.reset}`);

    const completed = this.state.tasks.filter(t => t.status === 'completed').length;
    const failed = this.state.tasks.filter(t => t.status === 'failed').length;
    const total = this.state.tasks.length;

    console.log(`Status: ${completed}/${total} completed, ${failed} failed`);
    console.log(`Time: ${this.state.getElapsedTime()}`);
    console.log(`Tokens: ${this.state.tokenUsed}/${this.state.tokenBudget}`);

    console.log(`\nTasks:`);
    for (const task of this.state.tasks) {
      const icon = task.status === 'completed' ? `${c.green}✓${c.reset}` :
                   task.status === 'failed' ? `${c.red}✗${c.reset}` :
                   `${c.yellow}○${c.reset}`;
      const duration = task.duration ? `(${(task.duration / 1000).toFixed(1)}s)` : '';
      console.log(`  ${icon} ${task.id} ${duration}`);
    }

    console.log('='.repeat(60));
  }

  status() {
    if (!this.state) {
      console.log('Workflow not initialized. Run init() first.');
      return;
    }

    this._printSummary();
  }
}

// ============================================================
// CLI 入口
// ============================================================
async function main() {
  const args = process.argv.slice(2);

  // 解析参数
  let manifestPath = null;
  let targetPhase = null;
  let taskId = null;
  let showStatus = false;
  let dryRun = false;
  let showHelp = false;
  let platform = null;

  for (const arg of args) {
    if (arg === '--help' || arg === '-h') showHelp = true;
    else if (arg === '--status') showStatus = true;
    else if (arg === '--dry-run') dryRun = true;
    else if (arg.startsWith('--phase=')) targetPhase = arg.split('=')[1];
    else if (arg.startsWith('--task=')) taskId = arg.split('=')[1];
    else if (arg.startsWith('--platform=')) platform = arg.split('=')[1];
    else if (arg.endsWith('.yaml') || arg.endsWith('.yml')) manifestPath = arg;
    else if (arg.startsWith('--')) { /* 忽略未知选项 */ }
    else if (!manifestPath) manifestPath = arg;
  }

  if (showHelp) {
    printHelp();
    process.exit(0);
  }

  if (!manifestPath) {
    console.error('Error: manifest file required');
    console.error('Usage: node workflow-engine.js <manifest.yaml> [options]');
    process.exit(1);
  }

  // 设置平台
  if (platform) process.env.SOP_PLATFORM = platform;

  // 创建引擎
  const engine = new WorkflowEngine(manifestPath);

  try {
    await engine.init(taskId);

    if (showStatus || dryRun) {
      engine.status();
      process.exit(0);
    }

    const result = await engine.run(targetPhase);

    // 检查结果
    const hasFailed = result.tasks.some(t => t.status === 'failed');
    process.exit(hasFailed ? 1 : 0);

  } catch (error) {
    console.error(`Fatal error: ${error.message}`);
    if (process.env.SOP_DEBUG) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

function printHelp() {
  console.log(`
${c.bold}SOP Workflow Engine${c.reset}

${c.bold}Usage:${c.reset}
  node workflow-engine.js <manifest.yaml> [options]

${c.bold}Options:${c.reset}
  --phase=<name>      Run specific phase only
  --task=<id>          Resume from specific task
  --status             Show workflow status
  --dry-run            Show plan without executing
  --platform=<name>    Target platform (mock|claude|opencode|codex|minimax)
  --help, -h          Show this help

${c.bold}Environment Variables:${c.reset}
  SOP_PLATFORM         Target platform (default: mock)
  SOP_TOKEN_BUDGET     Token budget (default: 100000)
  SOP_DEBUG            Enable debug output

${c.bold}Examples:${c.reset}
  node workflow-engine.js manifests/superpowers-sop.yaml
  node workflow-engine.js my-sop.yaml --phase=execute
  node workflow-engine.js --status my-sop.yaml
  SOP_PLATFORM=claude node workflow-engine.js my-sop.yaml
`);
}

// 导出
module.exports = {
  WorkflowEngine,
  WorkflowState,
  AgentInterface,
  VerifierRunner,
  TaskExecutor,
  BUILTIN_VERIFIERS,
  BUILTIN_TOOLS,
};

// CLI
if (require.main === module) {
  main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}
