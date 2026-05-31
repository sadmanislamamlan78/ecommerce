-- Phase 6 verification (run in SQL Editor after phase6_rls_security.sql)

-- Policies on core tables
SELECT schemaname, tablename, policyname, cmd, roles
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('products', 'orders', 'order_items', 'profiles', 'categories')
ORDER BY tablename, policyname;

-- Staff helper function exists
SELECT routine_name, routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'decrement_product_stock';

-- Sequence grants for product inserts
SELECT grantee, privilege_type
FROM information_schema.role_usage_grants
WHERE object_name = 'products_id_seq';
