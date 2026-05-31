# Create Storage Bucket via Dashboard (if SQL bucket step failed)

If `phase5_verify.sql` query 4 returns **no rows**, create the bucket manually:

1. Supabase Dashboard → **Storage** (left sidebar, folder icon)
2. Click **New bucket**
3. Settings:
   - **Name:** `product-images`
   - **Public bucket:** ON (enabled)
   - **File size limit:** 5 MB (optional)
   - **Allowed MIME types:** image/jpeg, image/png, image/webp, image/gif (optional)
4. Click **Create bucket**

Then re-run only the storage policies section from `phase5_admin.sql` (lines 53–82).
