-- 購入した商品へのレビュー(☆1〜5 と本文)を付けられるようにする。
--
-- レビューは購入1件につき1つなので、別テーブルにせず purchases の rating / comment に保存する
-- (どちらも初期スキーマから存在するが、これまで使われていなかった列)。
--   rating    : ☆の数(1〜5)。null ならレビュー未投稿
--   comment   : レビュー本文(任意)
--   update_at : レビューを投稿・最後に編集した日時
--
-- 新しい列は足さず、update_at をレビューの日時として使う。
-- そのため、レビュー以外の処理(購入履歴の非表示など)では update_at を更新しないこと。
--
-- 書き込み(投稿・編集・削除)はバックエンドから purchases を直接更新する(reviews/routes.py)。
-- 一覧は「平均・件数・ページ分の行」を1回で返すため関数 get_product_reviews にまとめる
-- (PostgREST の集計関数は Supabase の初期設定では無効なため)。

begin;

alter table purchases
  add constraint purchases_rating_range check (rating between 1 and 5);

comment on column purchases.update_at is
  'レビュー(rating / comment)を投稿・最後に編集した日時。レビュー以外の処理では更新しないこと';

-- 商品ごとのレビュー一覧を新しい順に取り出すための索引
create index purchases_reviews_idx
  on purchases (chatbot_id, update_at desc, purchase_id desc)
  where rating is not null;

commit;

-- ============================================================
-- 商品のレビュー一覧
-- ============================================================
--
-- 商品が出品中でない・出品者が退会済みなら null を返す(商品詳細 API と同じく見つからない扱い)。
-- 退会したユーザーのレビューは表示しない。
-- purchases.is_deleted は購入履歴の非表示用なので、レビューの表示には影響させない。
--
-- 戻り値: {"rating_avg": 4.3 | null, "review_count": 件数,
--          "reviews": [{username, rating, comment, reviewed_at}, ...]}
-- reviewed_at には purchases.update_at を入れる。

create or replace function get_product_reviews(
  p_chatbot_id uuid,
  p_limit integer,
  p_offset integer
)
returns jsonb
language sql
stable
set search_path = public
as $$
  with visible as (
    select p.purchase_id, u.username, p.rating, p.comment, p.update_at as reviewed_at
    from purchases p
    join users u on u.user_id = p.buyer_id
    where p.chatbot_id = p_chatbot_id
      and p.rating is not null
      and u.is_withdrawn = false
  ),
  page as (
    select * from visible
    order by reviewed_at desc, purchase_id desc
    limit p_limit offset p_offset
  )
  select case
    when not exists (
      select 1 from chatbot b
      join users s on s.user_id = b.creator_id
      where b.chatbot_id = p_chatbot_id
        and b.is_listed = true
        and s.is_withdrawn = false
    ) then null
    else jsonb_build_object(
      'rating_avg', (select round(avg(rating), 1) from visible),
      'review_count', (select count(*) from visible),
      'reviews', coalesce(
        (select jsonb_agg(
           jsonb_build_object(
             'username', username,
             'rating', rating,
             'comment', comment,
             'reviewed_at', reviewed_at
           )
           order by reviewed_at desc, purchase_id desc
         ) from page),
        '[]'::jsonb
      )
    )
  end;
$$;

revoke execute on function get_product_reviews(uuid, integer, integer) from public, anon, authenticated;
grant execute on function get_product_reviews(uuid, integer, integer) to service_role;
