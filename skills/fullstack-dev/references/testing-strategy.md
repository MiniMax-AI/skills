# Backend Testing Strategy

Comprehensive testing guide for backend and full-stack applications. Covers the full testing pyramid with deep focus on API integration tests, database testing, contract testing, and performance testing.

## Quick Start Checklist

- [ ] **Test runner configured** (Jest/Vitest, Pytest, Go test)
- [ ] **Test database** ready (Docker container or in-memory)
- [ ] **Database isolation** per test (transaction rollback or truncation)
- [ ] **Test factories** for common entities (user, order, product)
- [ ] **Auth helper** to generate tokens for tests
- [ ] **CI pipeline** runs tests with real database service
- [ ] **Coverage threshold** enforced (≥ 80%)

---

## The Testing Pyramid

```
         ╱╲        E2E (few, slow) — full flows across services
        ╱  ╲
       ╱────╲       Integration (moderate) — API + DB + external
      ╱      ╲
     ╱────────╲      Unit (many, fast) — pure business logic
    ╱__________╲
```

| Level | What | Speed | Count |
|-------|------|-------|-------|
| Unit | Pure functions, business logic, no I/O | < 10ms | 70%+ of tests |
| Integration | API routes + real database + mocked externals | 50-500ms | ~20% |
| E2E | Full user flow across deployed services | 1-30s | ~10% |
| Contract | API compatibility between services | < 100ms | Per API boundary |
| Performance | Load, stress, soak | Minutes | Per critical path |

---

## 1. API Integration Testing (CRITICAL)

### What to Test for Every Endpoint

| Aspect | Tests to Write |
|--------|---------------|
| Happy path | Correct input → expected response + correct DB state |
| Auth | No token → 401, bad token → 401, expired → 401 |
| Authorization | Wrong role → 403, not owner → 403 |
| Validation | Missing fields → 422, bad types → 422, boundary values |
| Not found | Invalid ID → 404, deleted resource → 404 |
| Conflict | Duplicate create → 409, stale update → 409 |
| Idempotency | Same request twice → same result |
| Side effects | DB state changed, events emitted, cache invalidated |
| Error format | All errors match RFC 9457 envelope |

### TypeScript (Jest + Supertest)

```typescript
describe('POST /api/orders', () => {
  let token: string;
  let product: Product;

  beforeAll(async () => {
    await resetDatabase();
    const user = await createTestUser({ role: 'customer' });
    token = await getAuthToken(user);
    product = await createTestProduct({ price: 29.99, stock: 10 });
  });

  it('creates order → 201 + correct DB state', async () => {
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [{ productId: product.id, quantity: 2 }] });

    expect(res.status).toBe(201);
    expect(res.body.data.total).toBe(59.98);

    const updated = await db.product.findUnique({ where: { id: product.id } });
    expect(updated!.stock).toBe(8);
  });

  it('rejects without auth → 401', async () => {
    const res = await request(app).post('/api/orders').send({ items: [] });
    expect(res.status).toBe(401);
  });

  it('rejects empty items → 422', async () => {
    const res = await request(app)
      .post('/api/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({ items: [] });
    expect(res.status).toBe(422);
    expect(res.body.errors[0].field).toBe('items');
  });
});
```

### Python (Pytest + FastAPI TestClient)

```python
@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_create_order_success(client, auth_headers, test_product):
    response = client.post("/api/orders", json={
        "items": [{"product_id": test_product.id, "quantity": 2}]
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["data"]["total"] == 59.98

def test_create_order_no_auth(client):
    response = client.post("/api/orders", json={"items": []})
    assert response.status_code == 401

def test_create_order_empty_items(client, auth_headers):
    response = client.post("/api/orders", json={"items": []}, headers=auth_headers)
    assert response.status_code == 422
```

---

## 2. Database Testing (HIGH)

### Test Isolation Strategies

| Strategy | Speed | Realism | When |
|----------|-------|---------|------|
| **Transaction rollback** | ⚡ Fastest | Medium | Default for unit + integration |
| **Truncation** | Fast | High | When rollback isn't possible |
| **Test containers** | Slow startup | Highest | CI pipeline, full integration |

**Transaction rollback (recommended default):**
```typescript
let tx: Transaction;
beforeEach(async () => { tx = await db.beginTransaction(); });
afterEach(async () => { await tx.rollback(); });
```

**Docker test containers (CI):**
```yaml
# docker-compose.test.yml
services:
  test-db:
    image: postgres:16-alpine
    tmpfs: /var/lib/postgresql/data   # RAM disk for speed
    environment:
      POSTGRES_DB: myapp_test
```

### Test Factories (Not Raw SQL)

```typescript
// factories/user.factory.ts
import { faker } from '@faker-js/faker';

export function buildUser(overrides: Partial<User> = {}): CreateUserDTO {
  return {
    email: faker.internet.email(),
    firstName: faker.person.firstName(),
    role: 'customer',
    ...overrides,
  };
}
export async function createUser(overrides = {}) {
  return db.user.create({ data: buildUser(overrides) });
}
```

```python
# factories/user_factory.py
import factory
from faker import Faker

class UserFactory(factory.Factory):
    class Meta:
        model = User
    email = factory.LazyAttribute(lambda _: Faker().email())
    first_name = factory.LazyAttribute(lambda _: Faker().first_name())
    role = "customer"
```

---

## 3. External Service Testing (HIGH)

### HTTP-Level Mocking (Not Function Mocking)

**TypeScript (nock):**
```typescript
import nock from 'nock';

it('processes payment successfully', async () => {
  nock('https://api.stripe.com')
    .post('/v1/charges')
    .reply(200, { id: 'ch_123', status: 'succeeded', amount: 5000 });

  const result = await paymentService.charge({ amount: 50.00, currency: 'usd' });
  expect(result.status).toBe('succeeded');
});

it('handles payment timeout', async () => {
  nock('https://api.stripe.com').post('/v1/charges').delay(10000).reply(200);
  await expect(paymentService.charge({ amount: 50, currency: 'usd' }))
    .rejects.toThrow('timeout');
});
```

**Python (responses):**
```python
import responses

@responses.activate
def test_payment_success():
    responses.post("https://api.stripe.com/v1/charges",
                   json={"id": "ch_123", "status": "succeeded"}, status=200)
    result = payment_service.charge(amount=50.00, currency="usd")
    assert result.status == "succeeded"
```

### Test Containers for Infrastructure

```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';
import { RedisContainer } from '@testcontainers/redis';

beforeAll(async () => {
  const pg = await new PostgreSqlContainer('postgres:16').start();
  process.env.DATABASE_URL = pg.getConnectionUri();
  await runMigrations();
}, 60000);
```

---

## 4. Contract Testing (MEDIUM-HIGH)

### Consumer-Driven Contracts (Pact)

**Consumer (OrderService calls UserService):**
```typescript
it('can fetch user by ID', async () => {
  await pact.addInteraction()
    .given('user usr_123 exists')
    .uponReceiving('GET /users/usr_123')
    .withRequest('GET', '/api/users/usr_123')
    .willRespondWith(200, (b) => {
      b.jsonBody({ data: { id: MatchersV3.string(), email: MatchersV3.email() } });
    })
    .executeTest(async (mockserver) => {
      const user = await new UserClient(mockserver.url).getUser('usr_123');
      expect(user.id).toBeDefined();
    });
});
```

**Provider verifies in CI:**
```typescript
await new Verifier({
  providerBaseUrl: 'http://localhost:3001',
  pactBrokerUrl: process.env.PACT_BROKER_URL,
  provider: 'UserService',
}).verifyProvider();
```

---

## 5. Performance Testing (MEDIUM)

### k6 Load Test

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },    // ramp up
    { duration: '1m',  target: 100 },   // sustain
    { duration: '30s', target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/orders`);
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

### Performance Budgets

| Metric | Target | Action if Exceeded |
|--------|--------|--------------------|
| p95 response time | < 500ms | Optimize queries/caching |
| p99 response time | < 1000ms | Check outlier queries |
| Error rate | < 0.1% | Investigate spikes |
| DB query time | < 100ms each | Add indexes |

### When to Run

| Trigger | Test Type |
|---------|-----------|
| Before major release | Full load test |
| New DB query/index | Query benchmark |
| Infrastructure change | Baseline comparison |
| Weekly (CI) | Smoke load test |

---

## Test File Organization

```
tests/
  unit/                      # Pure logic, mocked dependencies
    order.service.test.ts
  integration/               # API + real DB
    orders.api.test.ts
    auth.api.test.ts
  contracts/                 # Consumer-driven contracts
    user-service.consumer.pact.ts
  performance/               # Load tests
    load-test.js
  fixtures/
    factories/               # Test data factories
      user.factory.ts
    seeds/
      test-data.ts
  helpers/
    setup.ts                 # Global test config
    auth.helper.ts           # Token generation
    db.helper.ts             # DB cleanup
```

---

## Anti-Patterns

| # | ❌ Don't | ✅ Do Instead |
|---|---------|--------------|
| 1 | Test only happy paths | Test errors, auth, validation, edge cases |
| 2 | Mock everything (no real DB) | Use test containers or test DB |
| 3 | Tests depend on execution order | Each test sets up / tears down own state |
| 4 | Hardcode test data | Use factories (faker + overrides) |
| 5 | Test implementation details | Test behavior: input → output |
| 6 | Share mutable state | Isolate per test (transaction rollback) |
| 7 | Skip migration testing in CI | Run migrations from scratch in CI |
| 8 | No performance test before release | Load test every major release |
| 9 | Test against production data | Generated test data only |
| 10 | Test suite > 10 minutes | Parallelize, RAM disk, optimize setup |

---

## Common Issues

### Issue 1: "Tests pass alone but fail together"

**Cause:** Shared database state between tests. Missing cleanup.

**Fix:**
```typescript
beforeEach(async () => { await db.raw('TRUNCATE orders, users CASCADE'); });
// OR use transaction rollback per test
```

### Issue 2: "Jest did not exit one second after test run"

**Cause:** Unclosed database connections or HTTP servers.

**Fix:**
```typescript
afterAll(async () => {
  await db.destroy();
  await server.close();
});
```

### Issue 3: "Async callback was not invoked within timeout"

**Cause:** Missing `async/await` or unhandled promise.

**Fix:**
```typescript
// ❌ Promise not awaited
it('should work', () => { request(app).get('/users'); });

// ✅ Properly awaited
it('should work', async () => { await request(app).get('/users'); });
```

### Issue 4: "Integration tests too slow in CI"

**Fix:**
1. Use `tmpfs` for PostgreSQL data dir (RAM disk)
2. Run migrations once in `beforeAll`, truncate in `beforeEach`
3. Parallelize test suites with `--maxWorkers`
4. Skip performance tests on feature branches (only main)
