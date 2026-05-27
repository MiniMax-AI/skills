# Manifest Format Reference

## Full Schema

```yaml
meta:
  name: "workflow-name"

config:
  model: "MiniMax/MiniMax"           # LLM model (optional)
  adversarial_mode: true              # FAIL stops workflow (default: false)
  token_budget: 100000               # Global token budget
  token_budget_warning: 0.8          # Warning threshold (0-1)
  verifier_max_retries: 2            # Max adversarial retry rounds per task
  timeouts:
    wave: 600000                     # Wave-level timeout in ms (10 min)
    build: 300000                    # Per-task timeout (5 min)
    execute_per_task: 600000         # Fallback task timeout

phases:
  <phase-name>:
    name: "Human-readable Phase Name"
    tasks:
      - id: "unique-task-id"
        title: "Task Title"
        description: |                # This is the SPEC — worker implements this
          Detailed specification of what the worker should produce.
          The verifier checks against this description.
        agent_role: "worker"          # or "impl", "reviewer"
        depends_on: ["task-id"]      # DAG dependency (optional)
        verifier: "spec-compliance"  # Verifier type (optional, inherits from config)
        timeout: 300000              # Task-level timeout override (ms)
```

## Phase Structure

Phases execute **sequentially**. Tasks within a phase execute in parallel waves.

```yaml
phases:
  design:   # Phase 1: sequential
    tasks: [...]
  build:    # Phase 2: sequential
    tasks: [...]
  test:     # Phase 3: sequential
    tasks: [...]
```

## Task Dependencies

Dependencies form a DAG. The system computes waves via Kahn's algorithm:

```yaml
tasks:
  - id: "t1"           # Wave 0
  - id: "t2"           # Wave 0 (parallel with t1)
  - id: "t3"; depends_on: ["t1"]      # Wave 1
  - id: "t4"; depends_on: ["t1","t2"] # Wave 1
  - id: "t5"; depends_on: ["t3","t4"] # Wave 2
```

Wave execution:
- Wave 0: t1, t2 in parallel
- Wave 1: t3, t4 in parallel (after Wave 0 completes)
- Wave 2: t5 (after Wave 1 completes)

## Cross-phase Dependencies

Tasks depending on tasks in other phases are treated as pre-satisfied (the other phase has already completed):

```yaml
phases:
  setup:
    tasks:
      - id: "scaffold"
  build:
    tasks:
      - id: "build-a"; depends_on: ["scaffold"]  # treated as Wave 0
```

## Verifier Configuration

```yaml
config:
  verifiers:
    spec-compliance:
      threshold: 3.0
      model: "MiniMax-M2.7-highspeed"
    code_quality:
      threshold: 3.5
      model: "MiniMax-M2.7-highspeed"
```

## Evidence Commands

Worker output can embed bash commands that are auto-executed before verification:

````markdown
Here is the implementation:

```bash
npm install
npm test
```
````

Each ` ```bash ` block is extracted and executed. Exit code 0 = PASS, non-zero = FAIL.

## Task Description as SPEC

The `description` field is the authoritative specification. The verifier checks whether the worker's output implements the description exactly. Write descriptions that are:

- **Complete**: specify all inputs, outputs, and behaviors
- **Verifiable**: can be checked by a reviewer or automated test
- **Self-contained**: no missing context

## Full Example

```yaml
meta:
  name: "feature-flag-service"
config:
  adversarial_mode: true
  token_budget: 500000
  verifier_max_retries: 2

phases:
  build:
    name: "Build Feature Flag Service"
    tasks:
      - id: "data-model"
        title: "Data Model"
        description: |
          Create a Node.js module `flag-store.js` that:
          - Exports a `FeatureFlagStore` class
          - Constructor accepts `{ dataPath: string }`
          - Methods: `get(flag: string): boolean`, `set(flag: string, value: boolean): void`
          - Stores flags in a JSON file at dataPath
          - Auto-creates dataPath directory if missing
        agent_role: "worker"
        verifier: "spec-compliance"

      - id: "api-server"
        title: "API Server"
        description: |
          Create `server.js` that:
          - Uses Express, listens on PORT env var (default 3000)
          - GET /flags/:name → returns { flag, enabled } JSON
          - POST /flags/:name with body { enabled: boolean } → updates and returns updated flag
          - Imports and uses FeatureFlagStore from `./flag-store`
        agent_role: "worker"
        depends_on: ["data-model"]
        verifier: "spec-compliance"

      - id: "tests"
        title: "Unit Tests"
        description: |
          Create `test/flag-store.test.js` with:
          - Test that get() returns false for unknown flags
          - Test that set() followed by get() returns the set value
          - Test that flags persist after store re-instantiation
          Use any test framework (jest, tap, or node:test)
        agent_role: "worker"
        depends_on: ["data-model"]
```
