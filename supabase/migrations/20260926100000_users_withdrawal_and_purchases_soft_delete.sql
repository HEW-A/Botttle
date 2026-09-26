-- users に退会フラグ・退会日時、purchases に削除フラグ・削除日時を追加する。
--
-- users:
--   withdrawn_at は定義書にはあるがテーブルに未実装だったもの。
--   is_withdrawn は定義書・テーブルともに未実装だったもの。
-- purchases:
--   購入履歴を物理削除せず論理削除するために is_deleted / deleted_at を持たせる。

alter table users
  add column is_withdrawn boolean not null default false,
  add column withdrawn_at timestamp with time zone;

alter table purchases
  add column is_deleted boolean not null default false,
  add column deleted_at timestamp with time zone;
