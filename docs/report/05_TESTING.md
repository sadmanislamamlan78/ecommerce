# 5. Testing

## 5.1 Automated tests (Django)

Run from project root:

```bash
.\venv\Scripts\python.exe manage.py test
```

### Test modules (Phase 6)

| Module | Tests cover |
|--------|-------------|
| `apps.common.tests` | Validators, friendly error messages |
| `apps.accounts.tests` | Register/profile/login forms, profile auth |
| `apps.products.tests` | Checkout address validation, admin form, staff gate |
| `apps.cart.tests` | Add/update/remove cart (mocked Supabase) |
| `apps.orders.tests` | Checkout flow, anonymous protection |

**Minimum:** 5+ test cases — project includes **15+** across modules.

_[Paste terminal output showing `OK` and test count.]_

## 5.2 Manual test checklist

| # | Test | Expected |
|---|------|----------|
| 1 | Register new user | Profile created in Supabase |
| 2 | Login / logout | Session cleared on logout |
| 3 | Add to cart over stock | Error message |
| 4 | Checkout with empty cart | Redirect to shop |
| 5 | Checkout with invalid address | Form errors on page |
| 6 | View order history | Only own orders |
| 7 | Staff: create product | Success; appears in shop |
| 8 | Non-staff: open `/manage/` | Redirect home + permission message |
| 9 | Guest: `/orders/` | Redirect to login |
| 10 | Shop invalid category in URL | Ignored / no crash |

## 5.3 Security tests

- [ ] Confirm non-staff cannot INSERT into `products` via API (Supabase client test optional)
- [ ] Confirm user A cannot read user B orders (RLS)
- [ ] Confirm profile update cannot set `is_staff = true` without already being staff
