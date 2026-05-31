-- Run this AFTER phase5_admin.sql to SEE results in the Results panel below
-- Each query shows a table you can read

-- 1) Check is_staff column exists on profiles
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'profiles'
  AND column_name = 'is_staff';

-- 2) Check your staff users (should show is_staff = true)
SELECT id, full_name, is_staff
FROM profiles
WHERE is_staff = true;

-- 3) Check product RLS policies (should show 3 staff policies + read policy)
SELECT schemaname, tablename, policyname, cmd, roles
FROM pg_policies
WHERE tablename = 'products'
ORDER BY policyname;

-- 4) Check storage bucket exists
SELECT id, name, public, file_size_limit
FROM storage.buckets
WHERE id = 'product-images';

-- 5) Check storage policies
SELECT policyname, cmd, roles
FROM pg_policies
WHERE tablename = 'objects'
  AND schemaname = 'storage'
ORDER BY policyname;
