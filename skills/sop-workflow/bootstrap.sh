#!/usr/bin/env bash
# ============================================================
# SOP Workflow Bootstrap Script
# 一键安装和初始化 SOP Workflow Skill
# ============================================================
# 
# 使用方式:
#   ./bootstrap.sh init              初始化当前项目
#   ./bootstrap.sh install           安装 skill 到 ~/.mavis/skills/
#   ./bootstrap.sh doctor            检查环境依赖
#   ./bootstrap.sh demo              运行演示
#
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log() {
    echo -e "${BLUE}[INFO]${RESET} $1"
}

success() {
    echo -e "${GREEN}[PASS]${RESET} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${RESET} $1"
}

error() {
    echo -e "${RED}[FAIL]${RESET} $1"
}

info() {
    echo -e "${MAGENTA}[STEP]${RESET} ${BOLD}$1${RESET}"
}

# ============================================================
# 路径配置
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="sop-workflow"
MAVIS_SKILLS_DIR="${HOME}/.mavis/skills"
TARGET_SKILL_DIR="${MAVIS_SKILLS_DIR}/${SKILL_NAME}"

# ============================================================
# 依赖检查
# ============================================================
check_dependencies() {
    info "检查环境依赖..."
    
    local missing=()
    
    # Node.js
    if ! command -v node &> /dev/null; then
        missing+=("node")
    else
        local node_version=$(node --version)
        success "Node.js: ${node_version}"
    fi
    
    # npm
    if ! command -v npm &> /dev/null; then
        missing+=("npm")
    else
        success "npm: $(npm --version)"
    fi
    
    # js-yaml
    if node -e "require('js-yaml')" 2>/dev/null; then
        success "js-yaml: installed"
    else
        missing+=("js-yaml")
    fi
    
    # jq (可选)
    if command -v jq &> /dev/null; then
        success "jq: $(jq --version)"
    else
        warn "jq: not found (optional)"
    fi
    
    # git (可选)
    if command -v git &> /dev/null; then
        success "git: $(git --version | cut -d' ' -f3)"
    else
        warn "git: not found (optional)"
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        error "缺少依赖: ${missing[*]}"
        echo ""
        echo "安装依赖:"
        echo "  npm install -g js-yaml"
        echo ""
        return 1
    fi
    
    success "所有依赖检查通过"
    return 0
}

# ============================================================
# 安装 Skill
# ============================================================
install_skill() {
    info "安装 ${SKILL_NAME} skill..."
    
    # 创建目录
    mkdir -p "${MAVIS_SKILLS_DIR}"
    
    # 复制文件
    if [ -d "${TARGET_SKILL_DIR}" ]; then
        warn "Skill 已存在，正在更新..."
        rm -rf "${TARGET_SKILL_DIR}.backup"
        mv "${TARGET_SKILL_DIR}" "${TARGET_SKILL_DIR}.backup"
    fi
    
    cp -r "${SCRIPT_DIR}" "${TARGET_SKILL_DIR}"
    
    # 安装 npm 依赖
    if [ -f "${TARGET_SKILL_DIR}/package.json" ]; then
        (cd "${TARGET_SKILL_DIR}" && npm install)
    fi
    
    # 设置执行权限
    chmod +x "${TARGET_SKILL_DIR}/bootstrap.sh" 2>/dev/null || true
    chmod +x "${TARGET_SKILL_DIR}/engines/"*.js 2>/dev/null || true
    
    success "Skill 安装完成: ${TARGET_SKILL_DIR}"
    
    # 创建符号链接到本地
    if [ "${SCRIPT_DIR}" != "${TARGET_SKILL_DIR}" ]; then
        ln -sf "${TARGET_SKILL_DIR}" "${SCRIPT_DIR}/installed"
    fi
}

# ============================================================
# 初始化项目
# ============================================================
init_project() {
    info "初始化 SOP Workflow 项目..."
    
    local project_dir="${1:-$(pwd)}"
    cd "${project_dir}"
    
    # 检查是否是 git 仓库
    if [ ! -d ".git" ]; then
        warn "当前目录不是 git 仓库，可能需要先初始化:"
        echo "  git init"
        echo ""
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # 创建目录结构
    info "创建目录结构..."
    mkdir -p .sop-workflow
    mkdir -p sop-manifests
    mkdir -p .sop-context
    
    # 创建示例 manifest
    if [ ! -f "sop-manifest.yaml" ]; then
        info "创建示例 SOP Manifest..."
        cat > "sop-manifest.yaml" << 'EOF'
# ============================================================
# SOP Manifest - 你的第一个 SOP
# ============================================================
#
# 修改这个文件来自定义你的工作流程
# 完整文档: ~/.mavis/skills/sop-workflow/SKILL.md
#
# ============================================================

meta:
  name: my-first-sop
  version: 1.0.0

config:
  adversarial_mode: true
  
  # 上下文隔离级别: strict | moderate | open
  context_isolation: strict
  
  # Token 预算 (超过会警告)
  token_budget: 50000
  
  # 各阶段超时 (毫秒)
  timeouts:
    planning: 120000    # 2 分钟
    execute: 300000    # 5 分钟
    review: 60000      # 1 分钟
  
  # Verifier 重试次数
  verifier_max_retries: 2

# 阶段定义
phases:
  # ----------------------------------------
  # 阶段 1: 规划
  # ----------------------------------------
  planning:
    name: 任务规划
    description: 澄清需求，制定计划
    tasks:
      - id: clarify
        title: 需求澄清
        description: |
          理解真实需求，向利益相关者提问。
          确认: 要解决的问题是什么? 成功标准是什么?
        agent_role: architect
        # 是否需要用户确认后才能进入下一任务
        require_approval: false
      
      - id: plan
        title: 制定计划
        description: |
          将任务拆解为 2-5 分钟的原子任务。
          每个任务指定: 文件路径、操作、验证步骤。
        agent_role: planner
        depends_on: clarify
        verifier: functional

  # ----------------------------------------
  # 阶段 2: 执行
  # ----------------------------------------
  execute:
    name: 功能开发
    description: 按计划执行开发任务
    tasks:
      - id: implement
        title: 实现功能
        description: |
          按照计划逐步实现功能。
          每完成一个小任务，验证它能正常工作。
        agent_role: worker
        depends_on: plan
        verifier: code_quality
      
      - id: test
        title: 编写测试
        description: |
          为核心逻辑编写单元测试。
          确保测试覆盖边界情况。
        agent_role: worker
        depends_on: implement
        verifier: test_coverage

  # ----------------------------------------
  # 阶段 3: 评审
  # ----------------------------------------
  review:
    name: 代码评审
    description: 综合评审交付物
    tasks:
      - id: security-check
        title: 安全审计
        description: 检查常见安全漏洞
        agent_role: verifier
        depends_on: test
        verifier: security
      
      - id: final-review
        title: 最终评审
        description: |
          全面评审交付物是否满足原始需求。
          评估: 质量、安全、性能、文档。
        agent_role: senior-reviewer
        depends_on: security-check
        verifier: comprehensive

# Verifier 类型定义 (可选，使用默认定义)
# 如需自定义，参考 engines/verifier-prompts.js
# verifier_types:
#   code_quality:
#     pass_threshold: 3.5
#     dimensions: ...

# 准入准出标准
entry_criteria:
  planning:
    - "需求文档存在"
    - "利益相关者已确认"
  execute:
    - "计划已评审通过"
    - "资源已分配"
  review:
    - "功能已完成"
    - "测试覆盖率 > 70%"

exit_criteria:
  planning:
    - "计划包含所有任务"
    - "风险已识别"
  execute:
    - "所有测试通过"
    - "代码审查通过"
  review:
    - "安全审计通过"
    - "文档完整"
EOF
        success "创建 sop-manifest.yaml"
    else
        warn "sop-manifest.yaml 已存在，跳过"
    fi
    
    # 创建上下文摘要
    if [ ! -f ".sop-context/summary.json" ]; then
        cat > ".sop-context/summary.json" << 'EOF'
{
  "version": "1.0.0",
  "created": "DATE_PLACEHOLDER",
  "project": "PROJECT_NAME_PLACEHOLDER",
  "phases": ["planning", "execute", "review"],
  "last_updated": "DATE_PLACEHOLDER"
}
EOF
        # 替换占位符
        sed -i.bak "s/DATE_PLACEHOLDER/$(date -u +%Y-%m-%dT%H:%M:%SZ)/g" ".sop-context/summary.json"
        sed -i.bak "s/PROJECT_NAME_PLACEHOLDER/$(basename $(pwd))/g" ".sop-context/summary.json"
        rm -f ".sop-context/summary.json.bak"
        success "创建 .sop-context/summary.json"
    fi
    
    # 创建 .gitignore
    if [ -d ".git" ] && [ -f ".gitignore" ]; then
        if ! grep -q ".sop-workflow" .gitignore; then
            echo "" >> .gitignore
            echo "# SOP Workflow" >> .gitignore
            echo ".sop-workflow/" >> .gitignore
            echo ".sop-workflow-state.json" >> .gitignore
            echo ".sop-context/" >> .gitignore
            success "更新 .gitignore"
        fi
    fi
    
    # 创建示例 prompts
    mkdir -p "sop-prompts"
    if [ ! -f "sop-prompts/planning.md" ]; then
        cat > "sop-prompts/planning.md" << 'EOF'
# 任务规划 Prompt

## 目标
将需求拆解为可执行的原子任务。

## 输出格式
每个任务:
```
### [task-id]: 任务名称
- 文件: <路径>
- 操作: <具体操作>
- 验证: <如何验证>
- 风险: <识别到的风险>
```

## 原则
- 每个任务 2-5 分钟
- 任务之间无依赖或依赖明确
- 先做风险最高的任务
EOF
        success "创建 sop-prompts/planning.md"
    fi
    
    echo ""
    success "项目初始化完成!"
    echo ""
    echo "接下来:"
    echo "  1. 编辑 sop-manifest.yaml 自定义你的流程"
    echo "  2. 运行: node ${TARGET_SKILL_DIR}/engines/workflow-engine.js sop-manifest.yaml"
    echo ""
}

# ============================================================
# 运行演示
# ============================================================
run_demo() {
    info "运行演示..."
    
    local demo_dir="/tmp/sop-workflow-demo-$$"
    mkdir -p "${demo_dir}"
    cd "${demo_dir}"
    
    # 初始化
    "${SCRIPT_DIR}/bootstrap.sh" init
    
    # 干跑
    log "执行干跑 (dry-run)..."
    node "${TARGET_SKILL_DIR}/engines/workflow-engine.js" "sop-manifest.yaml" --dry-run || true
    
    cd /
    rm -rf "${demo_dir}"
    
    success "演示完成!"
}

# ============================================================
# 环境诊断
# ============================================================
doctor() {
    info "运行环境诊断..."
    
    echo ""
    echo "=== 系统信息 ==="
    echo "OS: $(uname -s) $(uname -r)"
    echo "Shell: ${SHELL}"
    echo "User: $(whoami)"
    echo ""
    
    echo "=== 路径 ==="
    echo "Script: ${SCRIPT_DIR}"
    echo "Target: ${TARGET_SKILL_DIR}"
    echo "Skill Dir: ${MAVIS_SKILLS_DIR}"
    echo ""
    
    echo "=== 文件检查 ==="
    for file in "SKILL.md" "package.json" "engines/workflow-engine.js" "engines/test-engine.js"; do
        if [ -f "${SCRIPT_DIR}/${file}" ]; then
            success "${file}"
        else
            error "${file} (missing)"
        fi
    done
    
    echo ""
    check_dependencies
    
    echo ""
    echo "=== 权限检查 ==="
    if [ -w "${MAVIS_SKILLS_DIR}" ]; then
        success "Skill 目录可写"
    else
        error "Skill 目录不可写: ${MAVIS_SKILLS_DIR}"
        echo "修复: chmod 755 ${MAVIS_SKILLS_DIR}"
    fi
    
    echo ""
}

# ============================================================
# 卸载
# ============================================================
uninstall() {
    info "卸载 ${SKILL_NAME} skill..."
    
    if [ -d "${TARGET_SKILL_DIR}" ]; then
        rm -rf "${TARGET_SKILL_DIR}"
        success "已卸载: ${TARGET_SKILL_DIR}"
    else
        warn "Skill 未安装"
    fi
}

# ============================================================
# 帮助
# ============================================================
print_help() {
    cat << 'EOF'
SOP Workflow Bootstrap

用法:
    ./bootstrap.sh <command>

命令:
    init        初始化当前项目为 SOP Workflow 项目
    install     安装 skill 到 ~/.mavis/skills/
    doctor      检查环境依赖
    demo        运行演示
    uninstall   卸载 skill
    help        显示帮助

示例:
    ./bootstrap.sh install      # 安装 skill
    ./bootstrap.sh init         # 初始化项目
    ./bootstrap.sh doctor       # 检查环境

环境变量:
    SOP_PLATFORM       目标平台 (opencode|claude|codex|minimax)
    SOP_TOKEN_BUDGET   Token 预算 (默认: 100000)

文档:
    完整文档: SKILL.md
    引擎源码: engines/workflow-engine.js
    Verifier 库: engines/verifier-prompts.js
EOF
}

# ============================================================
# 主入口
# ============================================================
main() {
    local command="${1:-help}"
    
    case "${command}" in
        init)
            init_project "${2:-.}"
            ;;
        install)
            install_skill
            ;;
        doctor)
            doctor
            ;;
        demo)
            run_demo
            ;;
        uninstall|remove)
            uninstall
            ;;
        help|--help|-h)
            print_help
            ;;
        *)
            error "未知命令: ${command}"
            echo ""
            print_help
            exit 1
            ;;
    esac
}

main "$@"
