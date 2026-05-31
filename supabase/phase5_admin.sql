-- Phase 5: Admin staff flag, product CRUD policies, Supabase Storage
-- Run in Supabase SQL Editor (New query)

-- 1. Staff flag on profiles
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT false;

-- Make YOUR account staff (replace email with your login email):
-- UPDATE profiles SET is_staff = true
-- WHERE id = (SELECT id FROM auth.users WHERE email = 'your-email@example.com');
-- example staff 1
UPDATE profiles SET is_staff = true
WHERE id = (SELECT id FROM auth.users WHERE email = 'sadmanislamamlan78@gmail.com');

-- Or set via Supabase Dashboard → Authentication → Users → user → Raw user meta data:
-- { "is_staff": true }

-- 2. Product CRUD for staff only (public can still read)
DROP POLICY IF EXISTS "Staff can insert products" ON products;
DROP POLICY IF EXISTS "Staff can update products" ON products;
DROP POLICY IF EXISTS "Staff can delete products" ON products;

CREATE POLICY "Staff can insert products"
    ON products FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true)
    );

CREATE POLICY "Staff can update products"
    ON products FOR UPDATE TO authenticated
    USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true))
    WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true));

CREATE POLICY "Staff can delete products"
    ON products FOR DELETE TO authenticated
    USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true));

GRANT INSERT, UPDATE, DELETE ON products TO authenticated;
-- Required for auto-increment id on INSERT (without this: "permission denied for sequence products_id_seq")
GRANT USAGE, SELECT ON SEQUENCE products_id_seq TO authenticated;

-- 3. Storage bucket for product images (create if missing)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'product-images',
    'product-images',
    true,
    5242880,
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']
)
ON CONFLICT (id) DO UPDATE SET
    public = true,
    file_size_limit = 5242880,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif'];

-- 4. Storage policies
DROP POLICY IF EXISTS "Public read product images" ON storage.objects;
DROP POLICY IF EXISTS "Staff upload product images" ON storage.objects;
DROP POLICY IF EXISTS "Staff update product images" ON storage.objects;
DROP POLICY IF EXISTS "Staff delete product images" ON storage.objects;

CREATE POLICY "Public read product images"
    ON storage.objects FOR SELECT
    USING (bucket_id = 'product-images');

CREATE POLICY "Staff upload product images"
    ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'product-images'
        AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true)
    );

CREATE POLICY "Staff update product images"
    ON storage.objects FOR UPDATE TO authenticated
    USING (
        bucket_id = 'product-images'
        AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true)
    );

CREATE POLICY "Staff delete product images"
    ON storage.objects FOR DELETE TO authenticated
    USING (
        bucket_id = 'product-images'
        AND EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND is_staff = true)
    );

NOTIFY pgrst, 'reload schema';
