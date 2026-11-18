-- 商品一覧・商品詳細で表示するチャットボットのサムネイル保存先。
-- 閲覧はログイン不要のためpublicとし、アップロードはSecret Keyを持つ
-- バックエンド経由に限定する（ブラウザから直接アップロードしない）。
insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'chatbot_thumbnails',
  'chatbot_thumbnails',
  true,
  5242880,
  array['image/jpeg', 'image/png', 'image/webp']
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;
