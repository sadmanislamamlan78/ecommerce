# StyleHouse — Fashion E-Commerce (CSE472)

Django 5 + Supabase fashion e-commerce project (Fabrilife-inspired).

**Current status: Phase 6 complete** — RLS polish, validation, tests, documentation report structure.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 5 |
| Database | Supabase PostgreSQL (Phase 2+) |
| Auth | Supabase Auth REST API (email + password) |
| HTTP client | `requests` (compatible with Python 3.11–3.14) |
| Frontend | Django Templates, HTML, CSS, JavaScript |
| Session | Django sessions store Supabase JWT |

## Project Structure

```
ecommerce/
├── manage.py
├── requirements.txt
├── .env.example          ← copy to .env
├── ecommerce/            ← Django settings
├── apps/
│   ├── accounts/         ← Supabase auth (Phase 1)
│   ├── products/         ← Catalog (Phase 2)
│   ├── cart/             ← Cart (Phase 3)
│   └── orders/           ← Orders (Phase 4)
├── templates/
├── static/
└── supabase/             ← SQL scripts
```

---

## Phase 1 Setup Guide

### 1. Create a Supabase project

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. Click **New project** and choose a name (e.g. `stylehouse-ecommerce`).
3. Set a strong database password (save it for `.env`).

### 2. Find your Supabase URL and anon key

1. Open your project in the Supabase Dashboard.
2. Go to **Project Settings** (gear icon) → **API**.
3. Copy these values into your `.env` file:

| Variable | Where to find it |
|----------|------------------|
| `SUPABASE_URL` | **Project URL** — e.g. `https://abcdefgh.supabase.co` |
| `SUPABASE_ANON_KEY` | **Project API keys** → `anon` `public` key |

> **Important:** Never commit `.env` or share your `service_role` key publicly. The `anon` key is safe for client-side use; Django uses it server-side in Phase 1.

### 3. Configure Supabase Auth

1. In Dashboard → **Authentication** → **Providers** → enable **Email**.
2. For easier university testing, you can disable email confirmation:
   - **Authentication** → **Providers** → Email → turn off **Confirm email**
   - Or leave it on and confirm via the link Supabase sends.

### 4. Run profiles SQL

In **SQL Editor**, paste and run:

```
supabase/phase1_profiles.sql
```

This creates the `profiles` table and Row Level Security (RLS) policies.

### 5. Local Django setup

```bash
# From project root
cd "e:\Web Assigment\ecommerce"

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Recommended: Python 3.11 or 3.12 (also works on 3.14 with this setup)

pip install -r requirements.txt

copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env`:

```env
SECRET_KEY=generate-a-random-50-char-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

USE_SUPABASE_DB=False
```

Generate a Django secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Run migrations (Django internal tables — sessions, admin):

```bash
python manage.py migrate
python manage.py runserver
```

Open: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Testing Authentication (Phase 1 Checklist)

| # | Test | Expected result |
|---|------|-----------------|
| 1 | Visit `/accounts/register/` | Registration form loads |
| 2 | Register with valid email + password (8+ chars) | Success message; redirected to profile |
| 3 | Sign out, then `/accounts/login/` | Login form loads |
| 4 | Login with same credentials | Welcome message; profile shows email |
| 5 | Visit `/accounts/profile/` while logged out | Redirect to login with `?next=` |
| 6 | Update profile (name, phone, address) | Saved in Supabase `profiles` table |
| 7 | Visit `/orders/` while logged out | Redirect to login (protected route) |
| 8 | Submit register with mismatched passwords | Form error shown |
| 9 | Login with wrong password | "Invalid email or password" |
| 10 | Check Supabase Dashboard → Authentication → Users | New user appears |

### Verify in Supabase

- **Authentication → Users** — your test account
- **Table Editor → profiles** — row with matching `id` and `full_name`

---

## How Auth Works

1. **Register/Login** — Django calls `supabase.auth.sign_up()` / `sign_in_with_password()`.
2. **Session** — Access + refresh tokens stored in Django session (HTTP-only cookie).
3. **Middleware** — `SupabaseAuthMiddleware` validates JWT on each request via `auth.get_user()`.
4. **Templates** — Use `request.supabase_user` and `request.session.supabase_email`.
5. **Protected routes** — `/orders/` requires login (more routes added in Phase 3–4).

---

## URLs (Phase 1)

| URL | Description |
|-----|-------------|
| `/` | Home (placeholder) |
| `/accounts/register/` | Sign up |
| `/accounts/login/` | Sign in |
| `/accounts/logout/` | Sign out |
| `/accounts/profile/` | User profile (login required) |
| `/cart/` | Cart placeholder |
| `/orders/` | Orders placeholder (login required) |

---

## Phase 2 Setup Guide

### 1. Run catalog SQL

In Supabase **SQL Editor**, run:

```
supabase/phase2_catalog.sql
```

This creates `categories` and `products` tables, RLS policies, and 12 sample products.

### 2. Verify tables

- **Table Editor** → `categories` (Men, Women, Kids)
- **Table Editor** → `products` (12 rows)

### 3. Test in Django

```bash
python manage.py runserver
```

| Page | URL |
|------|-----|
| Home (featured products) | http://127.0.0.1:8000/ |
| Shop (all + filters) | http://127.0.0.1:8000/shop/ |
| Product detail | http://127.0.0.1:8000/product/classic-cotton-tshirt/ |

### 4. Test filters

- Search by name (e.g. "dress")
- Category chips: Men / Women / Kids
- Price range sliders → **Apply Filters**
- Combine search + category + price

---

## Phase 5 — Admin CRUD (Staff only)

### 1. Run admin SQL

In Supabase **SQL Editor**, run `supabase/phase5_admin.sql`  
If **create product** fails with `permission denied for sequence products_id_seq`, also run `supabase/phase5_fix_product_insert.sql`

### 2. Make your account staff

Replace email in SQL, then run:

```sql
UPDATE profiles SET is_staff = true
WHERE id = (SELECT id FROM auth.users WHERE email = 'your-email@example.com');
```

**Sign out and sign in again** so `is_staff` loads into your session.

### 3. Admin URLs

| URL | Description |
|-----|-------------|
| `/manage/` | Product list dashboard (user menu → **Admin**) |
| `/manage/add/` | Add product + image upload |
| `/manage/<id>/edit/` | Edit product |
| `/manage/<id>/delete/` | Delete product |

Note: `/admin/` is reserved for Django’s built-in admin, not the shop product manager.

### 4. Storage bucket

SQL creates public bucket `product-images`. Images upload to Supabase Storage and save the public URL on the product.

Optional in `.env`:

```env
SUPABASE_STORAGE_BUCKET=product-images
```

---

## Phase 6 — Polish & Security

### 1. Run RLS security SQL

In Supabase **SQL Editor**, run:

```
supabase/phase6_rls_security.sql
```

Optional verification: `supabase/phase6_verify.sql`

This script:

- Removes the old “any authenticated user can UPDATE products” policy
- Keeps **staff-only** product INSERT/UPDATE/DELETE
- Secures orders, order_items, and profiles (users cannot self-promote to staff)
- Adds `decrement_product_stock()` for safe stock updates at checkout

### 2. Run automated tests

```bash
.\venv\Scripts\python.exe manage.py test
```

Tests live in `apps/common/tests.py`, `apps/accounts/tests.py`, `apps/products/tests.py`, `apps/cart/tests.py`, `apps/orders/tests.py`.

### 3. Documentation report

Fill in the report template under **`docs/report/`** (cover page + 7 sections) for your CSE472 submission.

### 4. Shared validation & errors

| Module | Purpose |
|--------|---------|
| `apps/common/validators.py` | Names, phone, address, shop filters, cart qty |
| `apps/common/errors.py` | User-friendly Supabase/RLS error messages |

---

## Next steps (optional)

- Deploy to Render / PythonAnywhere (see `docs/report/06_DEPLOYMENT.md`)

---

## Deployment Notes (later)

- Set `DEBUG=False`, strong `SECRET_KEY`, and `ALLOWED_HOSTS` on Render/PythonAnywhere
- Add environment variables in hosting dashboard (same as `.env`)
- Run `python manage.py collectstatic`

## License

University project — CSE472 Web and Internet Programming.
