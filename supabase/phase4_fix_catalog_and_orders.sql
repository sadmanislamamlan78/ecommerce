-- FIX: Products not showing + checkout save errors
-- Run this in Supabase SQL Editor (New query) after phase2_catalog + phase4 scripts

-- 1. Schema grants (anon = shop browse, authenticated = checkout)
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON categories TO anon, authenticated;
GRANT SELECT ON products TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON orders TO authenticated;
GRANT SELECT, INSERT ON order_items TO authenticated;
GRANT SELECT, INSERT, UPDATE ON profiles TO authenticated;
GRANT UPDATE ON products TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE orders_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE order_items_id_seq TO authenticated;

-- 2. Categories RLS (public read)
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read categories" ON categories;
DROP POLICY IF EXISTS "Anyone can view categories" ON categories;
CREATE POLICY "Anyone can view categories"
    ON categories FOR SELECT
    TO anon, authenticated
    USING (true);

-- 3. Products RLS (public read + authenticated can update stock on checkout)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public read products" ON products;
DROP POLICY IF EXISTS "Anyone can view products" ON products;
DROP POLICY IF EXISTS "Authenticated users can update products" ON products;
CREATE POLICY "Anyone can view products"
    ON products FOR SELECT
    TO anon, authenticated
    USING (true);
CREATE POLICY "Authenticated users can update products"
    ON products FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- 4. Orders RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own orders" ON orders;
DROP POLICY IF EXISTS "Users can create own orders" ON orders;
DROP POLICY IF EXISTS "Users can update own orders" ON orders;
CREATE POLICY "Users can view own orders"
    ON orders FOR SELECT TO authenticated
    USING (auth.uid() = user_id);
CREATE POLICY "Users can create own orders"
    ON orders FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own orders"
    ON orders FOR UPDATE TO authenticated
    USING (auth.uid() = user_id);

-- 5. Order items RLS
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own order items" ON order_items;
DROP POLICY IF EXISTS "Users can insert own order items" ON order_items;
CREATE POLICY "Users can view own order items"
    ON order_items FOR SELECT TO authenticated
    USING (order_id IN (SELECT id FROM orders WHERE user_id = auth.uid()));
CREATE POLICY "Users can insert own order items"
    ON order_items FOR INSERT TO authenticated
    WITH CHECK (order_id IN (SELECT id FROM orders WHERE user_id = auth.uid()));

-- 6. Profiles RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT TO authenticated
    USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT TO authenticated
    WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE TO authenticated
    USING (auth.uid() = id);

NOTIFY pgrst, 'reload schema';
