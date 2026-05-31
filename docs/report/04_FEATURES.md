# 4. Features Implemented

## 4.1 Customer features

| Feature | URL | Notes |
|---------|-----|-------|
| Home | `/` | Featured products |
| Shop | `/shop/` | Search, category, price filters |
| Product detail | `/product/<slug>/` | Add to cart |
| Cart | `/cart/` | Session cart + AJAX |
| Checkout | `/cart/checkout/` | Login required |
| Order history | `/orders/` | Login required |
| Profile | `/accounts/profile/` | Update shipping info |

## 4.2 Staff admin

| Feature | URL |
|---------|-----|
| Dashboard | `/manage/` |
| Add product | `/manage/add/` |
| Edit / delete | `/manage/<id>/edit/`, `/manage/<id>/delete/` |

## 4.3 Input validation (Phase 6)

- **Forms:** Django `Form` classes with `clean_*` methods
- **Shared validators:** `apps/common/validators.py`
- **Shop query params:** sanitized search, category slug, price range
- **Cart quantities:** clamped 1–99
- **Images:** type and 5 MB limit on admin upload

## 4.4 Error handling

- User-friendly messages via `apps/common/errors.py`
- Maps RLS, sequence permission, duplicate slug, SSL errors

_[Add screenshots for each major screen.]_
