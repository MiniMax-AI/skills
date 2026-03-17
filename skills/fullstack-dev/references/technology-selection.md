# Technology Selection Framework

Structured decision framework for backend and full-stack technology choices. Prevents analysis paralysis while ensuring rigorous evaluation.

**Iron Law: NO TECHNOLOGY CHOICE WITHOUT EXPLICIT TRADE-OFF ANALYSIS.**

"I like it" and "it's trending" are not engineering arguments.

---

## Phase 1: Requirements Before Technology

### Non-Functional Requirements (Quantify!)

| Dimension | Question | Bad Answer | Good Answer |
|-----------|----------|-----------|-------------|
| Scale | How many concurrent users? | "Lots" | "1K concurrent, 500 RPS peak" |
| Latency | Acceptable p99 response time? | "Fast" | "< 200ms API, < 2s reports" |
| Availability | Required uptime? | "Always up" | "99.9% (8.7h downtime/year)" |
| Data volume | Expected storage growth? | "A lot" | "100GB/year, 10M rows" |
| Consistency | Strong vs eventual? | "Consistent" | "Strong for payments, eventual for feeds" |
| Compliance | Regulatory? | "Some" | "GDPR data residency EU, SOC 2 Type II" |

### Team Constraints

- Team size and seniority level
- What the team already knows well
- Can you hire for this stack? (check job market)
- Timeline pressure (days vs months to production)
- Budget for licenses, infrastructure, training

---

## Phase 2: Evaluation Matrix

Score each option 1-5 on weighted criteria:

| Criterion | Weight | Option A | Option B | Option C |
|-----------|--------|----------|----------|----------|
| Meets functional requirements | 5× | _ | _ | _ |
| Meets non-functional requirements | 5× | _ | _ | _ |
| Team expertise / learning curve | 4× | _ | _ | _ |
| Ecosystem maturity (libs, tools) | 3× | _ | _ | _ |
| Community & long-term viability | 3× | _ | _ | _ |
| Operational complexity | 3× | _ | _ | _ |
| Hiring pool availability | 2× | _ | _ | _ |
| Cost (license + infra + training) | 2× | _ | _ | _ |
| **Weighted Total** | | _ | _ | _ |

**Rules:**
- Any option scoring **1 on a 5× criterion** → automatically disqualified
- Options within **10%** of each other → choose what team knows best
- Options within **15%** → run a **time-boxed PoC** (2-5 days max)

---

## Phase 3: Decision Trees

### Backend Language / Framework

```
What type of project?
│
├─ REST/GraphQL API, rapid development
│   ├─ Team knows TypeScript → Node.js
│   │   ├─ Full-featured, enterprise patterns → NestJS
│   │   ├─ Lightweight, flexible → Fastify / Hono / Express
│   │   └─ Full-stack with React → Next.js API routes
│   ├─ Team knows Python
│   │   ├─ High-perf async API → FastAPI
│   │   ├─ Full-stack, admin-heavy → Django
│   │   └─ Lightweight → Flask / Litestar
│   └─ Team knows Java/Kotlin
│       ├─ Enterprise, large team → Spring Boot
│       └─ Lightweight, fast startup → Quarkus / Ktor
│
├─ High concurrency, systems-level
│   ├─ Microservices, network → Go
│   ├─ Extreme perf, safety → Rust (Axum / Actix)
│   └─ Fault tolerance → Elixir (Phoenix)
│
├─ Real-time (WebSocket, streaming)
│   ├─ Node.js ecosystem → Socket.io / ws
│   ├─ Scalable pub/sub → Elixir Phoenix
│   └─ Low-latency → Go / Rust
│
└─ ML / data-intensive
    └─ Python (FastAPI + ML libs)
```

### Database

```
What data model?
│
├─ Structured, relational, ACID
│   ├─ General purpose → PostgreSQL ← DEFAULT CHOICE
│   ├─ Read-heavy, MySQL ecosystem → MySQL / MariaDB
│   └─ Embedded / serverless edge → SQLite / Turso / D1
│
├─ Semi-structured, flexible schema
│   ├─ Document-oriented → MongoDB
│   ├─ Serverless document → DynamoDB / Firestore
│   └─ Search-heavy → Elasticsearch / OpenSearch
│
├─ Key-value / cache
│   ├─ In-memory + data structures → Redis / Valkey
│   └─ Planet-scale KV → DynamoDB / Cassandra
│
├─ Time-series → TimescaleDB / ClickHouse / InfluxDB
├─ Graph → Neo4j / Apache AGE (Postgres extension)
└─ Vector (AI embeddings) → pgvector / Pinecone / Qdrant
```

**Default:** Start with PostgreSQL. It handles 80% of use cases.

### Caching Strategy

| Pattern | Technology | When |
|---------|-----------|------|
| Application cache | Redis / Valkey | Sessions, frequent reads, rate limiting |
| HTTP cache | CDN (Cloudflare/Vercel) | Static assets, public API responses |
| Query cache | Materialized views | Complex aggregations, dashboards |
| In-process cache | LRU (in-memory) | Config, small lookup tables |
| Edge cache | Cloudflare KV / Vercel KV | Global low-latency reads |

### Message Queue / Event Streaming

| Pattern | Technology | When |
|---------|-----------|------|
| Task queue (background jobs) | BullMQ / Celery / SQS | Email, exports, payments |
| Event streaming (replay, audit) | Kafka / Redpanda | Event sourcing, real-time pipelines |
| Lightweight pub/sub | Redis Streams / NATS | Simple notifications, broadcasting |
| Request-reply (sync over async) | NATS / RabbitMQ RPC | Internal service calls |

### Hosting / Deployment

| Model | Technology | When |
|-------|-----------|------|
| Serverless (auto-scale) | Vercel / Cloudflare Workers / Lambda | Variable traffic, pay-per-use |
| Container (predictable) | Cloud Run / Render / Railway / Fly.io | Steady traffic, simple ops |
| Kubernetes (large scale) | EKS / GKE / AKS | 10+ services, team has K8s expertise |
| VPS (full control) | DigitalOcean / Hetzner / EC2 | Predictable workload, cost-sensitive |

---

## Phase 4: Decision Documentation

### ADR (Architecture Decision Record) Template

```markdown
# ADR-{NNN}: {Title}

## Status: Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}

## Context
What problem are we solving? What forces are at play?

## Decision
What did we choose and why?

## Evaluation
| Criterion | Weight | Chosen | Runner-up |
|-----------|--------|--------|-----------|

## Consequences
- Positive: ...
- Negative: ...
- Risks: ...

## Alternatives Rejected
- Option B: rejected because...
- Option C: rejected because...
```

---

## Common Stack Templates

### A: Startup / MVP (Speed)

| Layer | Choice | Why |
|-------|--------|-----|
| Language | TypeScript | One language front + back |
| Framework | Next.js (full-stack) or NestJS (API) | Fast iteration |
| Database | PostgreSQL (Supabase / Neon) | Managed, generous free tier |
| Auth | Better Auth / Clerk | No auth code to maintain |
| Cache | Redis (Upstash) | Serverless-friendly |
| Hosting | Vercel / Railway | Zero-config deploys |

### B: SaaS / Business App (Balance)

| Layer | Choice | Why |
|-------|--------|-----|
| Language | TypeScript or Python | Team preference |
| Framework | NestJS or FastAPI | Structured, testable |
| Database | PostgreSQL | Reliable, feature-rich |
| Queue | BullMQ (Redis) | Simple background jobs |
| Auth | OAuth 2.0 + JWT | Standard, flexible |
| Hosting | AWS ECS / Cloud Run | Scalable containers |
| Monitoring | Datadog / Grafana + Prometheus | Full observability |

### C: High-Performance (Scale)

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Go or Rust | Max throughput, low latency |
| Database | PostgreSQL + Redis + ClickHouse | OLTP + cache + analytics |
| Queue | Kafka / Redpanda | High-throughput streaming |
| Hosting | Kubernetes (EKS/GKE) | Fine-grained scaling |
| Monitoring | Prometheus + Grafana + Jaeger | Metrics + tracing |

### D: AI / ML Application

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Python (API) + TypeScript (frontend) | ML libs + modern UI |
| Framework | FastAPI + Next.js | Async + SSR |
| Database | PostgreSQL + pgvector | Relational + embeddings |
| Queue | Celery + Redis | ML job processing |
| Hosting | Modal / AWS GPU / Replicate | GPU access |

---

## Anti-Patterns

| # | ❌ Don't | ✅ Do Instead |
|---|---------|--------------|
| 1 | "X is trending on HN" | Evaluate against YOUR requirements |
| 2 | Resume-Driven Development | Choose what team can maintain |
| 3 | "Must scale to 1M users" (day 1) | Build for 10× current need, not 1000× |
| 4 | Evaluate for weeks | Time-box to 3-5 days, then decide |
| 5 | No decision documentation | Write ADR for every major choice |
| 6 | Ignore operational cost | Include deploy, monitor, debug cost |
| 7 | "We'll rewrite later" | Assume you won't. Choose carefully. |
| 8 | Microservices by default | Start monolith, extract when needed |
| 9 | Different DB per service (day 1) | One database, split when justified |
| 10 | "It worked at Google" | You're not Google. Scale to YOUR context. |

---

## Common Issues

### Issue 1: "Team can't agree on a framework"

**Fix:** Time-box to 3 days. Fill the evaluation matrix. If scores within 10%, pick what the majority knows. Document in ADR. Move on.

### Issue 2: "We picked X but it doesn't fit"

**Fix:** Sunk cost fallacy check. If < 2 weeks invested, switch now. If > 2 weeks, document pain points and plan phased migration.

### Issue 3: "Do we need microservices?"

**Fix:** Almost certainly no. Start with a well-structured monolith. Extract to services only when: (a) different scaling needs, (b) different team ownership, (c) different deployment cadence.
