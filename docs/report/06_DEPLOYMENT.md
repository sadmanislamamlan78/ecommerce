# 6. Deployment

## 6.1 Environment variables

```env
SECRET_KEY=<strong-random-key>
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=<anon-key>
# Optional server-only:
SUPABASE_SERVICE_ROLE_KEY=<never expose to browser>
```

## 6.2 Pre-deploy checklist

- [ ] Run all `supabase/phase*.sql` scripts on production Supabase project
- [ ] `python manage.py collectstatic`
- [ ] `DEBUG=False`, secure `SECRET_KEY`
- [ ] Disable open CORS if configured
- [ ] Create staff user via SQL `UPDATE profiles SET is_staff = true WHERE ...`

## 6.3 Hosting options

| Platform | Notes |
|----------|-------|
| Render | Free tier, set env vars in dashboard |
| PythonAnywhere | WSGI config for Django |
| Railway | Similar to Render |

_[Document steps you actually used, or write "planned for submission".]_

## 6.4 Post-deploy verification

- Home and shop load products
- Register + login work
- Checkout creates order in Supabase
- Staff admin works over HTTPS
