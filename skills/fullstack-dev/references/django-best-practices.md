# Django Best Practices

Production-grade guide for Django 5.x and Django REST Framework. 40+ rules across 8 categories.

## Core Principles (7 Rules)

```
1. ✅ Custom User model BEFORE first migration (can't change later)
2. ✅ One Django app per domain concept (users, orders, payments)
3. ✅ Fat models, thin views — business logic in models/managers, not views
4. ✅ Always use select_related/prefetch_related (prevent N+1)
5. ✅ Settings split by environment (base + dev + prod)
6. ✅ Test with pytest-django + factory_boy (not fixtures)
7. ✅ Never use runserver in production (Gunicorn + Nginx)
```

---

## 1. Project Structure (CRITICAL)

### App-Per-Domain

```
myproject/
├── config/                     # Project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── dev.py              # DEBUG=True, SQLite ok
│   │   └── prod.py             # DEBUG=False, Postgres, HTTPS
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/                  # Custom User model
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── services.py         # Business logic
│   │   ├── selectors.py        # Complex queries
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── factories.py
│   ├── orders/
│   └── payments/
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── docker-compose.yml
```

### Rules

```
✅ One app = one bounded context (users, orders, payments)
✅ Business logic in services.py / selectors.py, not views
✅ Each app has its own urls.py, admin.py, tests/

❌ Never put everything in one app
❌ Never import across app boundaries at the model level (use IDs)
❌ Never put business logic in views or serializers
```

---

## 2. Models & Migrations (CRITICAL)

### Custom User Model (Day 1!)

```python
# apps/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

# config/settings/base.py
AUTH_USER_MODEL = 'users.User'
```

**This MUST be done before `migrate`. Cannot change after.**

### Model Best Practices

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Order(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]

    def cancel(self):
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel order in {self.status} status")
        self.status = OrderStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
```

### Migration Rules

```
✅ Review migration SQL: python manage.py sqlmigrate app_name 0001
✅ Name migrations descriptively: --name add_status_index_to_orders
✅ Separate data migrations from schema migrations
✅ Non-destructive first: add column → backfill → remove old column

❌ Never edit or delete applied migrations
❌ Never use RunPython without reverse function
```

---

## 3. Views & Serializers — DRF (HIGH)

### Service Layer Pattern

```python
# apps/orders/services.py
from django.db import transaction

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, items_data: list[dict]) -> Order:
        total = sum(item['price'] * item['quantity'] for item in items_data)
        order = Order.objects.create(user=user, total=total)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, **item) for item in items_data
        ])
        return order

    @staticmethod
    def cancel_order(order_id: str, user) -> Order:
        order = Order.objects.select_for_update().get(id=order_id, user=user)
        order.cancel()
        return order
```

### Serializers

```python
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'status', 'total', 'items', 'created_at']
        read_only_fields = ['id', 'total', 'created_at']

class CreateOrderSerializer(serializers.Serializer):
    """Input-only serializer — separate from output."""
    items = serializers.ListField(
        child=serializers.DictField(), min_length=1, max_length=50,
    )
    def validate_items(self, items):
        for item in items:
            if item.get('quantity', 0) < 1:
                raise serializers.ValidationError("Quantity must be at least 1")
        return items
```

### Views (Thin!)

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    serializer = CreateOrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = OrderService.create_order(request.user, serializer.validated_data['items'])
    return Response({'data': OrderSerializer(order).data}, status=status.HTTP_201_CREATED)
```

### Rules

```
✅ Separate input serializers from output serializers
✅ Views only: validate → call service → serialize → respond
✅ Use @transaction.atomic for multi-model writes

❌ Never put business logic in views or serializers
❌ Never use ModelSerializer for write operations (too implicit)
```

---

## 4. Authentication (HIGH)

| Method | When | Frontend |
|--------|------|----------|
| Session | Same-domain, SSR, Django templates | Django templates / htmx |
| JWT | Different domain, SPA, mobile | React, Vue, mobile apps |
| OAuth2 | Third-party login, API consumers | Any |

### JWT Config (djangorestframework-simplejwt)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## 5. Performance Optimization (HIGH)

### N+1 Query Prevention

```python
# ❌ N+1: 1 query for orders + N queries for users
orders = Order.objects.all()
for o in orders:
    print(o.user.email)     # hits DB each iteration

# ✅ select_related (FK/OneToOne — JOIN)
orders = Order.objects.select_related('user').all()

# ✅ prefetch_related (ManyToMany/reverse FK — 2 queries)
orders = Order.objects.prefetch_related('items').all()

# ✅ Combined
orders = Order.objects.select_related('user').prefetch_related('items').all()
```

### Query Optimization Toolkit

```python
# Only fetch needed columns
User.objects.values('id', 'email')
User.objects.values_list('email', flat=True)

# Annotate instead of Python loops
from django.db.models import Count, Sum
Order.objects.annotate(item_count=Count('items'), revenue=Sum('items__price'))

# Bulk operations
OrderItem.objects.bulk_create([...])
Order.objects.filter(status='pending').update(status='cancelled')

# Database indexes
class Meta:
    indexes = [
        models.Index(fields=['user', 'status']),
        models.Index(fields=['-created_at']),
        models.Index(fields=['email'], condition=Q(is_active=True)),
    ]

# Pagination
from rest_framework.pagination import CursorPagination
class OrderPagination(CursorPagination):
    page_size = 20
    ordering = '-created_at'
```

### Caching

```python
from django.core.cache import cache

def get_product(product_id: str):
    cache_key = f'product:{product_id}'
    product = cache.get(cache_key)
    if product is None:
        product = Product.objects.get(id=product_id)
        cache.set(cache_key, product, timeout=300)
    return product
```

---

## 6. Testing (MEDIUM-HIGH)

### pytest-django + factory_boy

```python
# conftest.py
@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client
```

```python
# factories.py
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    username = factory.Sequence(lambda n: f'user{n}')

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'orders.Order'
    user = factory.SubFactory(UserFactory)
    total = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
```

```python
# test_views.py
@pytest.mark.django_db
class TestListOrders:
    def test_returns_user_orders(self, authenticated_client):
        OrderFactory.create_batch(3, user=authenticated_client.handler._force_user)
        response = authenticated_client.get('/api/orders/')
        assert response.status_code == 200
        assert len(response.data['data']) == 3

    def test_requires_authentication(self, api_client):
        response = api_client.get('/api/orders/')
        assert response.status_code == 401
```

---

## 7. Admin Customization (MEDIUM)

```python
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
```

---

## 8. Production Deployment (MEDIUM)

### Security Settings

```python
# settings/prod.py
DEBUG = False
ALLOWED_HOSTS = ['example.com', 'www.example.com']
CSRF_TRUSTED_ORIGINS = ['https://example.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### Deployment Stack

```
Nginx → Gunicorn → Django
         ↕
      PostgreSQL + Redis (cache)
         ↕
      Celery (background tasks)
```

```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  --access-logfile -
```

### WhiteNoise for Static Files

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # right after Security
    ...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Rules

```
✅ Gunicorn + Nginx (or Cloud Run / Railway)
✅ PostgreSQL (not SQLite)
✅ python manage.py check --deploy
✅ Sentry for error tracking

❌ Never use runserver in production
❌ Never use DEBUG=True in production
❌ Never use SQLite in production
```

---

## Anti-Patterns

| # | ❌ Don't | ✅ Do Instead |
|---|---------|--------------|
| 1 | Business logic in views | Service layer (`services.py`) |
| 2 | One giant app | App-per-domain |
| 3 | Default User model | Custom User before first migrate |
| 4 | No `select_related` | Always eager-load related objects |
| 5 | Django fixtures for tests | `factory_boy` factories |
| 6 | `settings.py` single file | Split: base + dev + prod |
| 7 | `runserver` in production | Gunicorn + Nginx |
| 8 | SQLite in production | PostgreSQL |
| 9 | `ModelSerializer` for writes | Explicit input serializer |
| 10 | Raw SQL in views | ORM querysets + `selectors.py` |

---

## Common Issues

### Issue 1: "Can't change User model after first migration"

**Fix:** If starting fresh: delete all migrations + DB, set custom User, re-migrate. If data exists: complex migration (use `django-allauth` or incremental field migration).

### Issue 2: "Serializer is too slow on large querysets"

**Fix:** Missing `select_related` / `prefetch_related` → N+1 queries.
```python
queryset = Order.objects.select_related('user').prefetch_related('items')
```

### Issue 3: "Circular import between apps"

**Fix:** Use string references: `models.ForeignKey('orders.Order', ...)` instead of importing the model class. For services, import inside the function.
