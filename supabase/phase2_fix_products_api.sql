-- Run this if categories show but products do not (API permissions + RLS)

-- Allow API roles to read tables
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON categories TO anon, authenticated;
GRANT SELECT ON products TO anon, authenticated;

-- Ensure RLS policies exist
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read categories" ON categories;
CREATE POLICY "Public read categories"
    ON categories FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "Public read products" ON products;
CREATE POLICY "Public read products"
    ON products FOR SELECT
    USING (true);

-- Reload PostgREST schema cache (Supabase picks this up automatically; wait ~30 sec)
