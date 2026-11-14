-- 購入処理とコイン残高取得の関数を追加する。
--
-- 購入では「残高確認 → purchases 追加 → coin_transaction 追加 → cart から削除」を行う。
-- Supabase の Python クライアントにはトランザクションが無いため、これを Python から
-- 順に呼ぶと、途中で失敗したときに「利用権だけ付与されてコインが減らない」状態が残ったり、
-- 同じ購入者の同時リクエスト(ダブルクリック・別タブ)で残高がマイナスになったりする。
-- そのため購入処理を1つの関数にまとめ、関数呼び出し1回 = 1トランザクションで実行する。
--
-- コインの扱い:
--   残高は coin_transaction.amount の合計で表す(users に残高列は持たない)。
--   購入時は購入者に「マイナスの金額」の行を、商品ごとに1行追加する。
--   related_id には対応する purchases.purchase_id を入れる。
--   手数料は無し。出品者への売上入金は今回は行わない。
--
-- エラーは RAISE EXCEPTION でメッセージにエラーコードを入れて返し、
-- バックエンド(purchases/routes.py)がメッセージを見て HTTP ステータスに変換する。
--
-- 両関数ともバックエンド(service_role)からのみ呼ぶ想定なので、
-- anon / authenticated からは実行できないようにする。

-- ============================================================
-- コイン残高
-- ============================================================

create or replace function get_coin_balance(p_user_id varchar)
returns integer
language sql
stable
set search_path = public
as $$
  select coalesce(sum(amount), 0)::integer
  from coin_transaction
  where user_id = p_user_id;
$$;

-- ============================================================
-- 購入
-- ============================================================
--
-- p_chatbot_ids:
--   null  … カート内の商品をまとめて購入する(GET /api/cart に表示される商品と同じ範囲)
--   配列  … 指定した商品を購入する(単品購入)
-- p_expected_total:
--   画面に表示していた合計金額。指定された場合、実際の合計と違えば購入しない
--   (表示から確定までの間に価格が変わったときに、知らない金額で買わせないため)。
--
-- 戻り値: {"purchases": [{purchase_id, chatbot_id, price}, ...], "total": 合計, "balance": 購入後の残高}

create or replace function purchase_chatbots(
  p_buyer_id varchar,
  p_chatbot_ids uuid[] default null,
  p_expected_total integer default null
)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_ids uuid[];
  v_item record;
  v_total integer;
  v_balance integer;
  v_type_id smallint;
  v_purchase_id uuid;
  v_purchases jsonb := '[]'::jsonb;
begin
  -- 同じ購入者の購入処理を1つずつ順番に実行させるため、購入者の行をロックする。
  -- 2つ目のリクエストは1つ目のトランザクションが終わるまでここで待つので、
  -- 残高確認・購入済み確認の結果が古くなることがない。
  perform 1 from users
  where user_id = p_buyer_id and is_withdrawn = false
  for update;
  if not found then
    raise exception 'USER_NOT_FOUND';
  end if;

  if p_chatbot_ids is null then
    select coalesce(array_agg(c.chatbot_id), '{}')
    into v_ids
    from cart c
    join chatbot b on b.chatbot_id = c.chatbot_id
    join users s on s.user_id = b.creator_id
    where c.user_id = p_buyer_id
      and b.is_listed = true
      and s.is_withdrawn = false;

    if cardinality(v_ids) = 0 then
      raise exception 'CART_EMPTY';
    end if;
  else
    -- 同じIDが複数含まれていても1回の購入として扱う
    select coalesce(array_agg(distinct id), '{}') into v_ids from unnest(p_chatbot_ids) as id;

    if cardinality(v_ids) = 0 then
      raise exception 'PRODUCT_NOT_FOUND';
    end if;
  end if;

  -- 購入できる商品か1件ずつ確認する(1件でも購入できなければ全体を購入しない)
  for v_item in
    select id, b.chatbot_id, b.creator_id, b.price
    from unnest(v_ids) as id
    left join chatbot b on b.chatbot_id = id
      and b.is_listed = true
      and exists (select 1 from users s where s.user_id = b.creator_id and s.is_withdrawn = false)
  loop
    if v_item.chatbot_id is null or v_item.price is null or v_item.price < 0 then
      raise exception 'PRODUCT_NOT_FOUND';
    end if;
    if v_item.creator_id = p_buyer_id then
      raise exception 'OWN_PRODUCT';
    end if;
    -- purchases.is_deleted は履歴の非表示用なので、購入済み判定には使わない
    if exists (
      select 1 from purchases
      where buyer_id = p_buyer_id and chatbot_id = v_item.chatbot_id
    ) then
      raise exception 'ALREADY_PURCHASED';
    end if;
  end loop;

  select coalesce(sum(price), 0)::integer into v_total
  from chatbot where chatbot_id = any(v_ids);

  if p_expected_total is not null and p_expected_total <> v_total then
    raise exception 'TOTAL_MISMATCH';
  end if;

  v_balance := get_coin_balance(p_buyer_id);
  if v_balance < v_total then
    raise exception 'INSUFFICIENT_BALANCE';
  end if;

  select type_id into v_type_id from coin_transaction_type where type_name = 'purchase';
  if v_type_id is null then
    raise exception 'COIN_TYPE_NOT_FOUND';
  end if;

  for v_item in
    select chatbot_id, price from chatbot where chatbot_id = any(v_ids) order by chatbot_id
  loop
    insert into purchases (chatbot_id, buyer_id, payment_method)
    values (v_item.chatbot_id, p_buyer_id, 'coin')
    returning purchase_id into v_purchase_id;

    insert into coin_transaction (user_id, amount, type_id, related_id)
    values (p_buyer_id, -v_item.price, v_type_id, v_purchase_id);

    v_purchases := v_purchases || jsonb_build_object(
      'purchase_id', v_purchase_id,
      'chatbot_id', v_item.chatbot_id,
      'price', v_item.price
    );
  end loop;

  delete from cart where user_id = p_buyer_id and chatbot_id = any(v_ids);

  return jsonb_build_object(
    'purchases', v_purchases,
    'total', v_total,
    'balance', v_balance - v_total
  );
end;
$$;

revoke execute on function get_coin_balance(varchar) from public, anon, authenticated;
revoke execute on function purchase_chatbots(varchar, uuid[], integer) from public, anon, authenticated;
grant execute on function get_coin_balance(varchar) to service_role;
grant execute on function purchase_chatbots(varchar, uuid[], integer) to service_role;
