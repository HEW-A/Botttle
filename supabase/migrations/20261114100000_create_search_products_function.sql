-- 商品検索用の関数 search_products を追加する。
--
-- 検索キーワードは呼び出し側(API)で空白区切りにして p_terms に渡す。
-- どれか1語でも bot_name か description に含まれていればヒットする(OR)。
-- 部分一致で、英字の大文字・小文字は区別しない。
--
-- 並び順(bot_name の一致を優先する):
--   1. bot_name が入力全体(p_query)と完全一致
--   2. bot_name に含まれる語の数が多い順
--   3. bot_name か description に含まれる語の数が多い順(全語ヒットが上に来る)
--   4. 新しい順(商品一覧APIと同じ)
--
-- 一致判定は like ではなく strpos を使うので、% や _ もそのままの文字として扱われ、
-- エスケープは不要。
--
-- 出品中で、出品者が退会していない商品だけを返す(商品一覧APIと同じ条件)。

create or replace function search_products(
  p_query text,
  p_terms text[],
  p_limit integer,
  p_offset integer
)
returns table (
  chatbot_id uuid,
  bot_name varchar,
  price integer,
  description text,
  thumbnail_url text,
  username varchar,
  category_name text
)
language sql
stable
set search_path = public
as $$
  select
    c.chatbot_id,
    c.bot_name,
    c.price,
    c.description,
    c.thumbnail_url,
    u.username,
    cat.category_name
  from chatbot c
  join users u on u.user_id = c.creator_id
  left join category cat on cat.category_id = c.category_id
  cross join lateral (
    select
      count(*) filter (
        where strpos(lower(c.bot_name), lower(t)) > 0
      ) as name_hits,
      count(*) filter (
        where strpos(lower(c.bot_name), lower(t)) > 0
           or strpos(lower(coalesce(c.description, '')), lower(t)) > 0
      ) as matched
    from unnest(p_terms) as t
  ) s
  where c.is_listed
    and not u.is_withdrawn
    and s.matched > 0
  order by
    (lower(c.bot_name) = lower(p_query)) desc,
    s.name_hits desc,
    s.matched desc,
    c.create_at desc,
    c.chatbot_id desc
  limit p_limit
  offset p_offset;
$$;
