# Release & Acceptance Checklist

6-gate release checklist for backend and full-stack applications. Prevents "it works on my machine" and "we forgot to check X" failures.

**Iron Law: NO RELEASE WITHOUT ALL GATES PASSING.**

---

## Release Gates Overview

```
Feature Complete
    ↓
Gate 1: Functional Acceptance        → Does it do what it should?
    ↓
Gate 2: Non-Functional Acceptance    → Is it fast, reliable, observable?
    ↓
Gate 3: Security Review              → Is it safe?
    ↓
Gate 4: Deployment Readiness         → Can we deploy and rollback safely?
    ↓
Gate 5: Release Execution            → Deploy with canary + monitoring
    ↓
Gate 6: Post-Release Validation      → Did it actually work in production?
```

---

## Gate 1: Functional Acceptance

**Question: Does it do what the requirements say?**

- [ ] All acceptance criteria from ticket/PRD have passing tests
- [ ] Happy path works end-to-end
- [ ] Edge cases tested (empty inputs, max lengths, Unicode)
- [ ] Error cases tested (invalid input, not found, timeout)
- [ ] Data integrity verified (CRUD cycle produces correct state)
- [ ] Backward compatibility confirmed (existing clients not broken)
- [ ] API contract matches OpenAPI spec
- [ ] Idempotency verified (retries don't create duplicates)

### Evidence Template

| Requirement | Test | Status | Notes |
|-------------|------|--------|-------|
| User can create order | `orders.api.test:creates order` | ✅ PASS | |
| Empty cart → error | `orders.api.test:rejects empty` | ✅ PASS | |
| Payment failure handled | `payments.test:handles decline` | ✅ PASS | |

---

## Gate 2: Non-Functional Acceptance

**Question: Is it fast, reliable, and observable?**

### Performance

- [ ] Response time within budget (p95 < ___ms) — measured, not assumed
- [ ] No N+1 queries (checked with query logging)
- [ ] New queries use indexes (`EXPLAIN ANALYZE`)
- [ ] Pagination works on large datasets
- [ ] Caching effective (hit rate > 80%)
- [ ] Connection pool healthy under load

### Reliability

- [ ] Graceful degradation when dependencies fail (circuit breaker)
- [ ] Retry logic works for transient failures
- [ ] All external calls have timeouts
- [ ] Rate limiting returns 429 correctly
- [ ] Health check endpoints verified (`/health`, `/ready`)

### Observability

- [ ] Structured logging with request ID (not `console.log`)
- [ ] Metrics exposed (request count, latency, error rate)
- [ ] Alerts configured (error spike, latency spike)
- [ ] Request tracing works end-to-end
- [ ] Dashboard updated for new feature

### Evidence

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| p95 response | < 500ms | ___ms | ✅/❌ |
| p99 response | < 1000ms | ___ms | ✅/❌ |
| Error rate (load) | < 0.1% | ___% | ✅/❌ |
| Throughput | > ___ RPS | ___ RPS | ✅/❌ |

---

## Gate 3: Security Review

**Question: Does this introduce vulnerabilities?**

### Input & Output

- [ ] All input validated server-side (never trust client)
- [ ] SQL injection prevented (parameterized queries only)
- [ ] XSS prevented (output encoding)
- [ ] File upload validated (type, size, name sanitized)
- [ ] Rate limiting on sensitive endpoints (login, reset, APIs)

### Auth & Data

- [ ] Protected endpoints require valid credentials
- [ ] Users can only access their own resources
- [ ] Admin routes require admin role
- [ ] Tokens expire (short-lived access + refresh)
- [ ] Passwords hashed (bcrypt/argon2, not MD5/SHA)
- [ ] Sensitive data not logged (passwords, tokens, PII)
- [ ] Secrets in env vars (not hardcoded)
- [ ] Error messages don't leak internals

### Dependencies

- [ ] No known vulnerabilities (`npm audit` / `pip audit` / `govulncheck`)
- [ ] Dependencies pinned in lockfile
- [ ] Unused dependencies removed

---

## Gate 4: Deployment Readiness

**Question: Can we deploy safely and roll back if needed?**

### Code

- [ ] All tests pass in CI (not "it passed locally")
- [ ] Linter clean, build succeeds
- [ ] Code reviewed and approved
- [ ] No unresolved TODO/FIXME/HACK

### Database

- [ ] Migration tested on staging with production-like data
- [ ] Down migration works (tested!)
- [ ] Migration is non-destructive (additive only)
- [ ] Migration timing estimated on production data size
- [ ] Backfill plan documented (if needed)

### Configuration

- [ ] New env vars documented in `.env.example`
- [ ] Env vars set in staging and verified
- [ ] Env vars set in production
- [ ] Feature flags configured (if applicable)

### Rollback Plan Template

```markdown
## Rollback Plan: [Feature]

### When to rollback
- Error rate > 1% sustained 5 minutes
- p99 latency > 3000ms sustained 10 minutes
- Critical business function broken

### Steps
1. Revert deploy: [command]
2. Rollback migration (if applied): [command]
3. Invalidate cache: [command]
4. Notify team: #incidents channel
5. Verify rollback: [verification steps]

### Estimated time: [X minutes]
### Data recovery: [procedure if data was modified]
```

---

## Gate 5: Release Execution

### Deployment Sequence

```
1. 📢 ANNOUNCE in release channel

2. 🗄️ DATABASE — Apply migration
   - Run migration
   - Verify completion
   - Check data integrity

3. 🚀 DEPLOY — Roll out code
   - Canary first (10% traffic)
   - Monitor 5 minutes
   - If OK → 50% → monitor → 100%
   - If NOT OK → STOP immediately

4. 🔍 SMOKE TEST
   - Health check → 200
   - Login works
   - Core operation works
   - No error spikes

5. ✅ ANNOUNCE "Release complete. Monitoring 30 min."
```

### Canary Decision Table

| Metric | Baseline | Canary OK | STOP | ROLLBACK |
|--------|----------|-----------|------|----------|
| Error rate | 0.05% | < 0.1% | 0.5% | > 1% |
| p95 latency | 300ms | < 500ms | 700ms | > 1000ms |

---

## Gate 6: Post-Release Validation

### Immediate (0-30 min)

- [ ] Health checks green on all instances
- [ ] Error rate within normal range
- [ ] Latency normal (p95, p99)
- [ ] Core user journey manually tested
- [ ] Logs clean — no unexpected errors
- [ ] Alerts silent

### Short-term (1-24 hours)

- [ ] No customer complaints
- [ ] Business metrics stable (conversion, revenue, signups)
- [ ] Memory/CPU stable (no creeping usage)
- [ ] Queue backlogs clear
- [ ] Database performance stable

### Post-Release Report Template

```markdown
## Release Report: [Feature]
- Deployed: [timestamp] by @[engineer]
- Duration: [minutes]

| Check | Status | Notes |
|-------|--------|-------|
| Health checks | ✅ | All healthy |
| Error rate | ✅ | 0.03% (baseline: 0.05%) |
| p95 latency | ✅ | 310ms (baseline: 300ms) |
| Core flow | ✅ | Order creation verified |

Issues found: None / [details]
Rollback used: No / Yes: [reason]
```

---

## Release Readiness Score

Score each gate **0-2**: (0 = not checked, 1 = partially, 2 = fully verified with evidence)

| Gate | Score |
|------|-------|
| 1. Functional Acceptance | /2 |
| 2. Non-Functional Acceptance | /2 |
| 3. Security Review | /2 |
| 4. Deployment Readiness | /2 |
| 5. Release Execution Plan | /2 |
| 6. Post-Release Validation Plan | /2 |
| **Total** | **/12** |

**Decision:**
- **12/12** → Ship it ✅
- **10-11** → Ship with documented exceptions + owner assigned
- **< 10** → Do NOT release. Fix gaps first.

---

## Common Rationalizations

| ❌ Excuse | ✅ Reality |
|----------|-----------|
| "It's a small change" | Small changes cause outages every day |
| "We tested locally" | Local ≠ production |
| "We'll fix it if it breaks" | You'll fix it at 3 AM. Prevent now. |
| "Deadline is today" | Broken code costs more than late code |
| "CI passed" | CI doesn't check everything. Run the checklist. |
| "We can always rollback" | Only if you planned and tested rollback |
| "We did this last time fine" | Survivorship bias. Checklist every time. |
