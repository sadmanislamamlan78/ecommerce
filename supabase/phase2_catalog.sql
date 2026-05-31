-- Phase 2: Categories & Products (run in Supabase SQL Editor)

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    image_url TEXT,
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RLS
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

-- API access for anon/authenticated roles (required for Data API)
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON categories TO anon, authenticated;
GRANT SELECT ON products TO anon, authenticated;

-- Sample categories
INSERT INTO categories (name, slug, description) VALUES
    ('Men', 'men', 'Men''s fashion and apparel'),
    ('Women', 'women', 'Women''s fashion and apparel'),
    ('Kids', 'kids', 'Kids'' clothing and accessories')
ON CONFLICT (slug) DO NOTHING;

-- Sample products (reliable image URLs via picsum.photos)
INSERT INTO products (name, slug, description, price, category_id, image_url, stock) VALUES
    (
        'Classic Cotton T-Shirt',
        'classic-cotton-tshirt',
        'Soft breathable cotton tee for everyday wear. Regular fit.',
        599.00,
        (SELECT id FROM categories WHERE slug = 'men'),
        'https://picsum.photos/seed/stylehouse-tshirt/600/800',
        50
    ),
    (
        'Slim Fit Denim Jeans',
        'slim-fit-denim-jeans',
        'Stretch denim jeans with a modern slim silhouette.',
        1899.00,
        (SELECT id FROM categories WHERE slug = 'men'),
        'https://picsum.photos/seed/stylehouse-jeans/600/800',
        35
    ),
    (
        'Linen Casual Shirt',
        'linen-casual-shirt',
        'Lightweight linen shirt perfect for summer days.',
        1299.00,
        (SELECT id FROM categories WHERE slug = 'men'),
        'https://picsum.photos/seed/stylehouse-linen/600/800',
        28
    ),
    (
        'Floral Summer Dress',
        'floral-summer-dress',
        'Elegant floral print dress with a relaxed flowing cut.',
        2199.00,
        (SELECT id FROM categories WHERE slug = 'women'),
        'https://picsum.photos/seed/stylehouse-dress/600/800',
        22
    ),
    (
        'High-Waist Palazzo Pants',
        'high-waist-palazzo-pants',
        'Comfortable wide-leg pants with a flattering high waist.',
        1599.00,
        (SELECT id FROM categories WHERE slug = 'women'),
        'https://picsum.photos/seed/stylehouse-palazzo/600/800',
        30
    ),
    (
        'Knit Cardigan',
        'knit-cardigan',
        'Cozy open-front cardigan for layering in cooler weather.',
        1750.00,
        (SELECT id FROM categories WHERE slug = 'women'),
        'https://picsum.photos/seed/stylehouse-cardigan/600/800',
        18
    ),
    (
        'Kids Graphic Hoodie',
        'kids-graphic-hoodie',
        'Fun graphic hoodie with soft fleece lining for kids.',
        899.00,
        (SELECT id FROM categories WHERE slug = 'kids'),
        'https://picsum.photos/seed/stylehouse-hoodie/600/800',
        40
    ),
    (
        'Kids Jogger Pants',
        'kids-jogger-pants',
        'Stretchy jogger pants for play and school.',
        749.00,
        (SELECT id FROM categories WHERE slug = 'kids'),
        'https://picsum.photos/seed/stylehouse-jogger/600/800',
        45
    ),
    (
        'Kids Polo Shirt',
        'kids-polo-shirt',
        'Smart casual polo shirt in vibrant colors.',
        649.00,
        (SELECT id FROM categories WHERE slug = 'kids'),
        'https://picsum.photos/seed/stylehouse-polo/600/800',
        55
    ),
    (
        'Premium Blazer',
        'premium-blazer',
        'Tailored blazer for formal and semi-formal occasions.',
        3499.00,
        (SELECT id FROM categories WHERE slug = 'men'),
        'https://picsum.photos/seed/stylehouse-blazer/600/800',
        12
    ),
    (
        'Silk Evening Top',
        'silk-evening-top',
        'Luxurious silk top with a refined drape.',
        1999.00,
        (SELECT id FROM categories WHERE slug = 'women'),
        'https://picsum.photos/seed/stylehouse-silk/600/800',
        15
    ),
    (
        'Kids Winter Jacket',
        'kids-winter-jacket',
        'Warm padded jacket to keep kids cozy in winter.',
        1599.00,
        (SELECT id FROM categories WHERE slug = 'kids'),
        'https://picsum.photos/seed/stylehouse-jacket/600/800',
        20
    )
ON CONFLICT (slug) DO NOTHING;
