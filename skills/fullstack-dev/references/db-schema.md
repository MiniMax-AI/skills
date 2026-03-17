---
name: fullstack-dev-db-schema
description: "Database schema design and migrations. Use when creating tables, defining ORM models, adding indexes, or designing relationships. Covers zero-downtime migrations and multi-tenancy."
license: MIT
metadata:
  version: "1.0.0"
  sources:
    - PostgreSQL official documentation
    - Use The Index, Luke (use-the-index-luke.com)
    - Designing Data-Intensive Applications (Martin Kleppmann)
    - Database Reliability Engineering (Laine Campbell & Charity Majors)
---

# Database Schema Design

ORM-agnostic guide for relational database schema design. Covers data modeling, normalization, indexing, migrations, multi-tenancy, and common application patterns. Primarily PostgreSQL-focused but principles apply to MySQL/MariaDB.

## Scope

**USE this skill when:**
- Designing a schema for a new project or feature
- Deciding between normalization and denormalization
- Choosing which indexes to create
- Planning a zero-downtime migration on a live database
- Implementing multi-tenant data isolation
- Adding audit trails, soft delete, or versioning
- Diagnosing slow queries caused by schema problems

**NOT for:**
- Choosing which database technology to use (→ `technology-selection`)
- PostgreSQL-specific query tuning (use PostgreSQL performance docs)
- ORM-specific configuration (→ `django-best-practices` or your ORM's docs)
- Application-layer caching (→ `fullstack-dev-practices`)

## Context Required

| Required | Optional |
|----------|----------|
| Database engine (PostgreSQL / MySQL) | Expected data volume (rows, growth rate) |
| Domain entities and relationships | Read/write ratio |
| Key access patterns (queries) | Multi-tenant requirements |

---

## Quick Start Checklist

Designing a new schema:

- [ ] **Domain entities identified** — map 1 entity = 1 table (not 1 class = 1 table)
- [ ] **Primary keys**: UUID for public IDs, serial/bigserial for internal-only
- [ ] **Foreign keys** with explicit `ON DELETE` behavior
- [ ] **NOT NULL** by default — nullable only when business logic requires it
- [ ] **Timestamps**: `created_at` + `updated_at` on every table
- [ ] **Indexes** created for every WHERE, JOIN, ORDER BY column
- [ ] **No premature denormalization** — start normalized, denormalize when measured
- [ ] **Naming convention** consistent: `snake_case`, plural table names

---

## Quick Navigation

| Need to… | Jump to |
|----------|---------|
| Model entities and relationships | [1. Data Modeling](#1-data-modeling-critical) |
| Decide normalize vs denormalize | [2. Normalization](#2-normalization-vs-denormalization-critical) |
| Choose the right index | [3. Indexing](#3-indexing-strategy-critical) |
| Run migrations safely on live DB | [4. Migrations](#4-zero-downtime-migrations-high) |
| Design multi-tenant schema | [5. Multi-Tenancy](#5-multi-tenant-design-high) |
| Add soft delete / audit trails | [6. Common Patterns](#6-common-schema-patterns-medium) |
| Partition large tables | [7. Partitioning](#7-table-partitioning-medium) |
| See anti-patterns | [Anti-Patterns](#anti-patterns) |

---

## Core Principles (7 Rules)

```
1. ✅ Start normalized (3NF) — denormalize only when you have measured evidence
2. ✅ Every table has a primary key, created_at, updated_at
3. ✅ UUID for public-facing IDs, serial for internal join keys
4. ✅ NOT NULL by default — null is a business decision, not a lazy default
5. ✅ Index every column used in WHERE, JOIN, ORDER BY
6. ✅ Foreign keys enforced in database (not just application code)
7. ✅ Migrations are additive — never drop/rename in production without a multi-step plan
```

---

## 1. Data Modeling (CRITICAL)

### Table Naming

```sql
-- ✅ Plural, snake_case
CREATE TABLE orders (...);
CREATE TABLE order_items (...);
CREATE TABLE user_profiles (...);

-- ❌ Singular, mixed case
CREATE TABLE Order (...);
CREATE TABLE OrderItem (...);
CREATE TABLE tbl_usr_prof (...);    -- cryptic abbreviation
```

### Primary Keys

| Strategy | When | Pros | Cons |
|----------|------|------|------|
| `bigserial` (auto-increment) | Internal tables, FK joins | Compact, fast joins | Enumerable, not safe for public IDs |
| `uuid` (v4 random) | Public-facing resources | Non-guessable, globally unique | Larger (16 bytes), random I/O on B-Tree |
| `uuid` v7 (time-sorted) | Public + needs ordering | Non-guessable + insert-friendly | Newer, less ecosystem support |
| `text` slug | URL-friendly resources | Human-readable | Must enforce uniqueness, updates expensive |

**Recommended default:**

```sql
CREATE TABLE orders (
    id          bigserial PRIMARY KEY,             -- internal FK target
    public_id   uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,  -- API-facing
    -- ...
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```

### Relationships

```sql
-- One-to-Many: user → orders
CREATE TABLE orders (
    id         bigserial PRIMARY KEY,
    user_id    bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- ...
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Many-to-Many: orders ↔ products (via junction table)
CREATE TABLE order_items (
    id         bigserial PRIMARY KEY,
    order_id   bigint NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id bigint NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity   int NOT NULL CHECK (quantity > 0),
    unit_price numeric(10,2) NOT NULL,
    UNIQUE (order_id, product_id)  -- prevent duplicate line items
);

-- One-to-One: user → profile
CREATE TABLE user_profiles (
    user_id    bigint PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio        text,
    avatar_url text,
    -- ...
);
```

### ON DELETE Behavior

| Behavior | When | Example |
|----------|------|---------|
| `CASCADE` | Child meaningless without parent | order_items when order deleted |
| `RESTRICT` | Prevent accidental deletion | products referenced by order_items |
| `SET NULL` | Preserve child, clear reference | orders.assigned_to when employee leaves |
| `SET DEFAULT` | Fallback to default value | Rare, for status columns |

---

## 2. Normalization vs Denormalization (CRITICAL)

### Start Normalized (3NF)

**Normal forms in practice:**

| Form | Rule | Example Violation |
|------|------|-------------------|
| 1NF | No repeating groups, atomic values | `tags = "go,python,rust"` in one column |
| 2NF | No partial dependencies (composite keys) | `order_items.product_name` depends on `product_id` alone |
| 3NF | No transitive dependencies | `orders.customer_city` depends on `customer_id`, not `order_id` |

**1NF violation fix:**
```sql
-- ❌ Tags as comma-separated string
CREATE TABLE posts (id serial, tags text);  -- tags = "go,python"

-- ✅ Separate table (or array/JSONB if simple)
CREATE TABLE post_tags (
    post_id bigint REFERENCES posts(id) ON DELETE CASCADE,
    tag_id  bigint REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- ✅ Alternative: PostgreSQL array (if tags are just strings, no metadata)
CREATE TABLE posts (id serial, tags text[] NOT NULL DEFAULT '{}');
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
```

### When to Denormalize

**Denormalize ONLY when:**
1. You have **measured** a performance problem (EXPLAIN ANALYZE, not "I think it's slow")
2. The denormalized data is **read-heavy** (read:write ratio > 100:1)
3. You accept the **consistency maintenance cost** (triggers, application logic, or materialized views)

**Safe denormalization patterns:**

```sql
-- Pattern 1: Materialized view (computed, refreshable)
CREATE MATERIALIZED VIEW order_summary AS
SELECT o.id, o.user_id, o.total,
       COUNT(oi.id) AS item_count,
       u.email AS user_email
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
JOIN users u ON u.id = o.user_id
GROUP BY o.id, u.email;

REFRESH MATERIALIZED VIEW CONCURRENTLY order_summary;  -- non-blocking

-- Pattern 2: Cached aggregate column (application-maintained)
ALTER TABLE orders ADD COLUMN item_count int NOT NULL DEFAULT 0;
-- Update via trigger or application code on order_item insert/delete

-- Pattern 3: JSONB snapshot (freeze-at-write-time)
-- Store a copy of the product details at the time of purchase
CREATE TABLE order_items (
    id          bigserial PRIMARY KEY,
    order_id    bigint NOT NULL REFERENCES orders(id),
    product_id  bigint REFERENCES products(id),
    quantity    int NOT NULL,
    unit_price  numeric(10,2) NOT NULL,      -- frozen price
    product_snapshot jsonb NOT NULL           -- frozen name, description, image
);
```

---

## 3. Indexing Strategy (CRITICAL)

### Index Types (PostgreSQL)

| Type | When | Example |
|------|------|---------|
| **B-Tree** (default) | Equality, range, ORDER BY | `WHERE status = 'active'`, `WHERE created_at > '2025-01-01'` |
| **Hash** | Equality only (rare, B-Tree usually better) | `WHERE id = 123` (large tables, Postgres 10+) |
| **GIN** | Arrays, JSONB, full-text search | `WHERE tags @> '{go}'`, `WHERE data->>'key' = 'val'` |
| **GiST** | Geometry, ranges, nearest-neighbor | PostGIS, tsrange, ltree |
| **BRIN** | Very large tables with natural ordering | Time-series data sorted by timestamp |

### Index Decision Rules

```
Rule 1: Index every column in WHERE clauses
Rule 2: Index every column used in JOIN ON conditions
Rule 3: Index every column in ORDER BY (if queried with LIMIT)
Rule 4: Composite index for multi-column WHERE (leftmost prefix rule)
Rule 5: Partial index when filtering a subset (e.g., only active records)
Rule 6: Covering index (INCLUDE) to avoid table lookup
Rule 7: DON'T index low-cardinality columns alone (e.g., boolean)
```

### Composite Index: Column Order Matters

```sql
-- Query: WHERE user_id = ? AND status = ? ORDER BY created_at DESC
-- ✅ Optimal: matches query pattern left-to-right
CREATE INDEX idx_orders_user_status_created
ON orders(user_id, status, created_at DESC);

-- ❌ Wrong order: can't use for this query efficiently
CREATE INDEX idx_orders_created_user_status
ON orders(created_at DESC, user_id, status);
```

**Leftmost prefix rule:** Index on `(A, B, C)` supports queries on `(A)`, `(A, B)`, `(A, B, C)` but NOT `(B)`, `(C)`, or `(B, C)`.

### Partial Index (Index Only What Matters)

```sql
-- Only 5% of orders are 'pending', but queried frequently
CREATE INDEX idx_orders_pending
ON orders(created_at DESC)
WHERE status = 'pending';

-- Only active users matter for login
CREATE INDEX idx_users_active_email
ON users(email)
WHERE is_active = true;
```

### Covering Index (Avoid Table Lookup)

```sql
-- Query only needs id and status, no need to read the table row
CREATE INDEX idx_orders_user_covering
ON orders(user_id) INCLUDE (status, total);

-- Now this query is index-only:
SELECT status, total FROM orders WHERE user_id = 123;
```

### When NOT to Index

```
❌ Columns rarely used in WHERE/JOIN/ORDER BY
❌ Tables with < 1,000 rows (sequential scan is faster)
❌ Columns with very low cardinality alone (e.g., boolean is_active)
❌ Write-heavy tables where index maintenance cost > read benefit
❌ Duplicate indexes (check pg_stat_user_indexes for unused indexes)
```

---

## 4. Zero-Downtime Migrations (HIGH)

### The Golden Rule

```
NEVER make destructive changes in one step.
Always: ADD → MIGRATE DATA → REMOVE OLD (in separate deploys).
```

### Safe Migration Patterns

**Rename a column (3 deploys):**

```
Deploy 1: Add new column
  ALTER TABLE users ADD COLUMN full_name text;
  UPDATE users SET full_name = name;           -- backfill
  -- App writes to BOTH name and full_name

Deploy 2: Switch reads to new column
  -- App reads from full_name, still writes to both

Deploy 3: Drop old column
  ALTER TABLE users DROP COLUMN name;
  -- App only uses full_name
```

**Add a NOT NULL column (2 deploys):**

```sql
-- Deploy 1: Add nullable column, backfill
ALTER TABLE orders ADD COLUMN currency text;              -- nullable first
UPDATE orders SET currency = 'USD' WHERE currency IS NULL; -- backfill

-- Deploy 2: Add constraint (after all rows backfilled)
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;
ALTER TABLE orders ALTER COLUMN currency SET DEFAULT 'USD';
```

**Add an index without locking:**

```sql
-- ✅ CONCURRENTLY: no table lock, can run on live DB
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);

-- ❌ Without CONCURRENTLY: locks table for writes during build
CREATE INDEX idx_orders_status ON orders(status);
```

### Migration Safety Checklist

```
✅ Migration runs in < 30 seconds on production data size
✅ No exclusive table locks (use CONCURRENTLY for indexes)
✅ Rollback plan documented and tested
✅ Backfill runs in batches (not one giant UPDATE)
✅ New column added as nullable first, constraint added later
✅ Old column kept until all code references removed

❌ Never rename/drop columns in one deploy
❌ Never ALTER TYPE on large tables without testing timing
❌ Never run data backfill in a transaction (OOM on large tables)
```

### Batch Backfill Template

```sql
-- Backfill in batches of 10,000 (avoids long-running transactions)
DO $$
DECLARE
  batch_size int := 10000;
  affected int;
BEGIN
  LOOP
    UPDATE orders
    SET currency = 'USD'
    WHERE id IN (
      SELECT id FROM orders WHERE currency IS NULL LIMIT batch_size
    );
    GET DIAGNOSTICS affected = ROW_COUNT;
    RAISE NOTICE 'Updated % rows', affected;
    EXIT WHEN affected = 0;
    PERFORM pg_sleep(0.1);  -- brief pause to reduce load
  END LOOP;
END $$;
```

---

## 5. Multi-Tenant Design (HIGH)

### Three Approaches

| Approach | Isolation | Complexity | When |
|----------|-----------|------------|------|
| **Row-level** (shared tables + `tenant_id`) | Low | Low | SaaS MVP, < 1,000 tenants |
| **Schema-per-tenant** | Medium | Medium | Regulated industries, moderate scale |
| **Database-per-tenant** | High | High | Enterprise, strict data isolation |

### Row-Level Tenancy (Most Common)

```sql
-- Every table has tenant_id
CREATE TABLE orders (
    id         bigserial PRIMARY KEY,
    tenant_id  bigint NOT NULL REFERENCES tenants(id),
    user_id    bigint NOT NULL REFERENCES users(id),
    total      numeric(10,2) NOT NULL,
    -- ...
);

-- Composite index: tenant first (most queries filter by tenant)
CREATE INDEX idx_orders_tenant_user ON orders(tenant_id, user_id);
CREATE INDEX idx_orders_tenant_status ON orders(tenant_id, status);

-- Row-Level Security (PostgreSQL)
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.tenant_id')::bigint);
```

**Application-level enforcement:**

```typescript
// Middleware: set tenant context on every request
app.use((req, res, next) => {
  const tenantId = req.headers['x-tenant-id'];
  if (!tenantId) return res.status(400).json({ error: 'Missing tenant' });
  req.tenantId = tenantId;
  next();
});

// Repository: ALWAYS filter by tenant
async findOrders(tenantId: string, userId: string) {
  return db.order.findMany({
    where: { tenantId, userId },  // ← tenant_id in EVERY query
  });
}
```

### Rules

```
✅ tenant_id in EVERY table that holds tenant data
✅ tenant_id as FIRST column in every composite index
✅ Application middleware enforces tenant context
✅ Use RLS (PostgreSQL) as defense-in-depth, not sole protection
✅ Test with 2+ tenants to verify isolation

❌ Never allow cross-tenant queries in application code
❌ Never skip tenant_id in WHERE clauses (even in admin tools)
```

---

## 6. Common Schema Patterns (MEDIUM)

### Soft Delete

```sql
ALTER TABLE orders ADD COLUMN deleted_at timestamptz;

-- All queries filter deleted records
CREATE VIEW active_orders AS
SELECT * FROM orders WHERE deleted_at IS NULL;

-- Partial index: only index non-deleted rows
CREATE INDEX idx_orders_active_status
ON orders(status, created_at DESC)
WHERE deleted_at IS NULL;
```

**ORM integration:**

```typescript
// Prisma middleware: auto-filter soft-deleted records
prisma.$use(async (params, next) => {
  if (params.action === 'findMany' || params.action === 'findFirst') {
    params.args.where = { ...params.args.where, deletedAt: null };
  }
  return next(params);
});
```

### Audit Trail

```sql
-- Option A: Audit columns on every table
ALTER TABLE orders ADD COLUMN created_by bigint REFERENCES users(id);
ALTER TABLE orders ADD COLUMN updated_by bigint REFERENCES users(id);

-- Option B: Separate audit log table (more detail)
CREATE TABLE audit_log (
    id          bigserial PRIMARY KEY,
    table_name  text NOT NULL,
    record_id   bigint NOT NULL,
    action      text NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data    jsonb,
    new_data    jsonb,
    changed_by  bigint REFERENCES users(id),
    changed_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);
```

### Enum Columns

```sql
-- Option A: PostgreSQL enum type (strict, but ALTER TYPE is painful)
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled');
ALTER TABLE orders ADD COLUMN status order_status NOT NULL DEFAULT 'pending';

-- Option B: Text + CHECK constraint (easier to migrate)
ALTER TABLE orders ADD COLUMN status text NOT NULL DEFAULT 'pending'
  CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'));

-- Option C: Lookup table (most flexible, best for UI-driven lists)
CREATE TABLE order_statuses (
    id    serial PRIMARY KEY,
    name  text UNIQUE NOT NULL,
    label text NOT NULL      -- display name
);
```

**Recommendation:** Option B (text + CHECK) for most cases. Option C if statuses are managed by non-developers.

### Polymorphic Associations

```sql
-- ❌ Anti-pattern: polymorphic FK (no referential integrity)
CREATE TABLE comments (
    id             bigserial PRIMARY KEY,
    commentable_type text,    -- 'Post' or 'Photo'
    commentable_id   bigint,  -- no FK constraint possible!
    body           text
);

-- ✅ Pattern A: Separate FK columns (nullable)
CREATE TABLE comments (
    id       bigserial PRIMARY KEY,
    post_id  bigint REFERENCES posts(id) ON DELETE CASCADE,
    photo_id bigint REFERENCES photos(id) ON DELETE CASCADE,
    body     text NOT NULL,
    CHECK (
      (post_id IS NOT NULL AND photo_id IS NULL) OR
      (post_id IS NULL AND photo_id IS NOT NULL)
    )
);

-- ✅ Pattern B: Separate tables (cleanest, best for different schemas)
CREATE TABLE post_comments (..., post_id bigint REFERENCES posts(id));
CREATE TABLE photo_comments (..., photo_id bigint REFERENCES photos(id));
```

### JSONB Columns (Semi-Structured Data)

```sql
-- Good uses: metadata, settings, flexible attributes
CREATE TABLE products (
    id         bigserial PRIMARY KEY,
    name       text NOT NULL,
    price      numeric(10,2) NOT NULL,
    attributes jsonb NOT NULL DEFAULT '{}'  -- color, size, weight...
);

-- Index for JSONB queries
CREATE INDEX idx_products_attrs ON products USING GIN(attributes);

-- Query
SELECT * FROM products WHERE attributes->>'color' = 'red';
SELECT * FROM products WHERE attributes @> '{"size": "XL"}';
```

```
✅ Use JSONB for truly flexible/optional data (metadata, settings, preferences)
✅ Index JSONB columns with GIN when queried

❌ Never use JSONB for data that should be columns (email, status, price)
❌ Never use JSONB to avoid schema design (it's not MongoDB-in-Postgres)
```

---

## 7. Table Partitioning (MEDIUM)

### When to Partition

```
✅ Table > 100M rows AND growing
✅ Most queries filter on the partition key (date range, tenant)
✅ Old data can be dropped/archived by partition (efficient DELETE)

❌ Table < 10M rows (overhead not worth it)
❌ Queries don't filter on partition key (scans all partitions)
```

### Range Partitioning (Time-Series)

```sql
CREATE TABLE events (
    id         bigserial,
    tenant_id  bigint NOT NULL,
    event_type text NOT NULL,
    payload    jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE events_2025_01 PARTITION OF events
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE events_2025_02 PARTITION OF events
  FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Automate partition creation with pg_partman or cron
```

### List Partitioning (Multi-Tenant)

```sql
CREATE TABLE orders (
    id        bigserial,
    tenant_id bigint NOT NULL,
    total     numeric(10,2)
) PARTITION BY LIST (tenant_id);

CREATE TABLE orders_tenant_1 PARTITION OF orders FOR VALUES IN (1);
CREATE TABLE orders_tenant_2 PARTITION OF orders FOR VALUES IN (2);
```

---

## Anti-Patterns

| # | ❌ Don't | ✅ Do Instead |
|---|---------|--------------|
| 1 | Premature denormalization | Start 3NF, denormalize when measured |
| 2 | Auto-increment IDs as public API identifiers | UUID for public, serial for internal |
| 3 | No foreign key constraints | FK enforced in database, always |
| 4 | Nullable by default | NOT NULL by default, nullable when required |
| 5 | No indexes on FK columns | Index every FK column |
| 6 | Single-step destructive migration | ADD → MIGRATE → REMOVE in separate deploys |
| 7 | `CREATE INDEX` without `CONCURRENTLY` | Always `CONCURRENTLY` on live tables |
| 8 | Polymorphic FK (`commentable_type + commentable_id`) | Separate FK columns or separate tables |
| 9 | JSONB for everything | JSONB for flexible data only, columns for structured |
| 10 | No `created_at` / `updated_at` | Timestamp pair on every table |
| 11 | Comma-separated values in one column | Separate table or PostgreSQL array |
| 12 | `text` without length validation | CHECK constraint or application validation |

---

## Common Issues

### Issue 1: "Query is slow but I already have an index"

**Symptom:** `EXPLAIN ANALYZE` shows Sequential Scan despite existing index.

**Causes:**
1. **Wrong index column order** — composite index `(A, B)` won't help `WHERE B = ?`
2. **Low selectivity** — index on boolean column (50% of rows match), planner prefers seq scan
3. **Stale statistics** — run `ANALYZE table_name;`
4. **Type mismatch** — comparing `varchar` column with `integer` parameter → no index use

**Fix:** Check `EXPLAIN (ANALYZE, BUFFERS)`, verify index matches query pattern, run `ANALYZE`.

### Issue 2: "Migration locks the table for minutes"

**Symptom:** `ALTER TABLE` blocks all writes during execution.

**Cause:** Adding NOT NULL constraint, changing column type, or creating index without `CONCURRENTLY`.

**Fix:**
```sql
-- Add index without lock
CREATE INDEX CONCURRENTLY idx_name ON table(col);

-- Add NOT NULL constraint without lock (Postgres 12+)
ALTER TABLE t ADD CONSTRAINT t_col_nn CHECK (col IS NOT NULL) NOT VALID;
ALTER TABLE t VALIDATE CONSTRAINT t_col_nn;  -- non-blocking validation
```

### Issue 3: "How many indexes is too many?"

**Rule of thumb:**
- Read-heavy table (reports, product catalog): 5-10 indexes is fine
- Write-heavy table (events, logs): 2-3 indexes max
- Monitor with `pg_stat_user_indexes` — drop indexes with `idx_scan = 0`

```sql
-- Find unused indexes
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname NOT LIKE '%pkey%'
ORDER BY pg_relation_size(indexrelid) DESC;
```
