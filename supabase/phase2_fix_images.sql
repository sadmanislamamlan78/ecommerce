-- Fix product images that don't load (run in Supabase SQL Editor → New query)
-- Uses picsum.photos — reliable placeholder photos for all 12 products

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-tshirt/600/800'
WHERE slug = 'classic-cotton-tshirt';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-jeans/600/800'
WHERE slug = 'slim-fit-denim-jeans';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-linen/600/800'
WHERE slug = 'linen-casual-shirt';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-dress/600/800'
WHERE slug = 'floral-summer-dress';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-palazzo/600/800'
WHERE slug = 'high-waist-palazzo-pants';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-cardigan/600/800'
WHERE slug = 'knit-cardigan';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-hoodie/600/800'
WHERE slug = 'kids-graphic-hoodie';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-jogger/600/800'
WHERE slug = 'kids-jogger-pants';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-polo/600/800'
WHERE slug = 'kids-polo-shirt';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-blazer/600/800'
WHERE slug = 'premium-blazer';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-silk/600/800'
WHERE slug = 'silk-evening-top';

UPDATE products SET image_url = 'https://picsum.photos/seed/stylehouse-jacket/600/800'
WHERE slug = 'kids-winter-jacket';
