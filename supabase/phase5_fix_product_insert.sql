-- Fix: staff cannot INSERT new products (permission denied for sequence products_id_seq)
-- Run once in Supabase SQL Editor after phase5_admin.sql

GRANT INSERT, UPDATE, DELETE ON products TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE products_id_seq TO authenticated;

NOTIFY pgrst, 'reload schema';
