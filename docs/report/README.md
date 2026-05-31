# StyleHouse — CSE472 Documentation Report

Use this folder as the **skeleton for your final written report**. Copy each section file into Word/Google Docs or merge into one PDF for submission.

## How to use

1. Fill in **student name**, **ID**, and **date** on the cover page.
2. Complete each numbered section with screenshots and short explanations.
3. Keep screenshots small but readable (Supabase dashboard, Django pages, tests).
4. Reference SQL files from `supabase/` when describing database setup.

## Report files

| File | Section |
|------|---------|
| [00_COVER.md](00_COVER.md) | Title page |
| [01_INTRODUCTION.md](01_INTRODUCTION.md) | Project overview & objectives |
| [02_SYSTEM_ARCHITECTURE.md](02_SYSTEM_ARCHITECTURE.md) | Stack, diagrams, folder structure |
| [03_DATABASE_AND_RLS.md](03_DATABASE_AND_RLS.md) | Tables, RLS, security |
| [04_FEATURES.md](04_FEATURES.md) | User & admin features |
| [05_TESTING.md](05_TESTING.md) | Manual + automated tests |
| [06_DEPLOYMENT.md](06_DEPLOYMENT.md) | Hosting & environment |
| [07_CONCLUSION.md](07_CONCLUSION.md) | Summary & future work |

## Suggested screenshots checklist

- [ ] Home page with featured products
- [ ] Shop with filters applied
- [ ] Cart and checkout success
- [ ] Order history (logged in)
- [ ] Admin product dashboard (`/manage/`)
- [ ] Supabase Table Editor (products, orders, profiles)
- [ ] Supabase Authentication users list
- [ ] SQL Editor after running `phase6_rls_security.sql`
- [ ] Terminal output: `python manage.py test`
