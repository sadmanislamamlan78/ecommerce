-- Phase 6: RLS polish & security (safe to re-run)
-- Run in Supabase SQL Editor after phase1–phase5 scripts

-- =============================================================================
-- 1. Helper: decrement stock on checkout (avoids open product UPDATE for all users)
-- =============================================================================
CREATE OR REPLACE FUNCTION public.decrement_product_stock(p_product_id INTEGER, p_quantity INTEGER)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF p_quantity IS NULL OR p_quantity < 1 THEN
        RETURN;
    END IF;
    UPDATE products
    SET stock = GREATEST(0, COALESCE(stock, 0) - p_quantity)
    WHERE id = p_product_id;
END;
$$;

REVOKE ALL ON FUNCTION public.decrement_product_stock(INTEGER, INTEGER) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.decrement_product_stock(INTEGER, INTEGER) TO authenticated;

-- =============================================================================
-- 2. Table grants (least privilege)
-- =============================================================================
GRANT USAGE ON SCHEMA public TO anon, authenticated;

GRANT SELECT ON categories TO anon, authenticated;
GRANT SELECT ON products TO anon, authenticated;

GRANT SELECT, INSERT, UPDATE ON profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE ON orders TO authenticated;
GRANT SELECT, INSERT ON order_items TO authenticated;

-- Staff product management (phase 5)
GRANT INSERT, UPDATE, DELETE ON products TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE products_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE orders_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE order_items_id_seq TO authenticated;

-- No direct writes for anonymous users
REVOKE INSERT, UPDATE, DELETE ON profiles FROM anon;
REVOKE INSERT, UPDATE, DELETE ON orders FROM anon;
REVOKE INSERT, UPDATE, DELETE ON order_items FROM anon;
REVOKE INSERT, UPDATE, DELETE ON products FROM anon;

-- =============================================================================
-- 3. Categories — public read only
-- =============================================================================
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read categories" ON categories;
DROP POLICY IF EXISTS "Anyone can view categories" ON categories;
CREATE POLICY "Anyone can view categories"
    ON categories FOR SELECT
    TO anon, authenticated
    USING (true);

-- =============================================================================
-- 4. Products — public read; staff CRUD; no blanket authenticated UPDATE
-- =============================================================================
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read products" ON products;
DROP POLICY IF EXISTS "Anyone can view products" ON products;
DROP POLICY IF EXISTS "Authenticated users can update products" ON products;
DROP POLICY IF EXISTS "Staff can insert products" ON products;
DROP POLICY IF EXISTS "Staff can update products" ON products;
DROP POLICY IF EXISTS "Staff can delete products" ON products;

CREATE POLICY "Anyone can view products"
    ON products FOR SELECT
    TO anon, authenticated
    USING (true);

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

-- =============================================================================
-- 5. Orders — users only see/create their own
-- =============================================================================
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
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- =============================================================================
-- 6. Order items — tied to user's orders
-- =============================================================================
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own order items" ON order_items;
DROP POLICY IF EXISTS "Users can insert own order items" ON order_items;

CREATE POLICY "Users can view own order items"
    ON order_items FOR SELECT TO authenticated
    USING (
        order_id IN (SELECT id FROM orders WHERE user_id = auth.uid())
    );

CREATE POLICY "Users can insert own order items"
    ON order_items FOR INSERT TO authenticated
    WITH CHECK (
        order_id IN (SELECT id FROM orders WHERE user_id = auth.uid())
    );

-- =============================================================================
-- 7. Profiles — own row only; users cannot grant themselves staff
-- =============================================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT TO authenticated
    WITH CHECK (
        auth.uid() = id
        AND COALESCE(is_staff, false) = false
    );

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (
        auth.uid() = id
        AND (
            COALESCE(is_staff, false) = false
            OR EXISTS (
                SELECT 1 FROM profiles AS p
                WHERE p.id = auth.uid() AND p.is_staff = true
            )
        )
    );

NOTIFY pgrst, 'reload schema';
