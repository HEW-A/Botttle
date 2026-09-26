-- カート機能用の cart、お気に入り機能用の favorite_bot を追加する。
--
-- 同じユーザーが同じチャットボットを二重にカート・お気に入りに入れられないよう
-- (user_id, chatbot_id) に UNIQUE 制約を付ける。
--
-- 注意:
--   主キーは smallserial のため、採番できるのは 1〜32767 まで。
--   行を削除しても番号は再利用されないので、カートの出し入れが多いと
--   いずれ上限に達する。足りなくなったら integer / bigint に変更すること。

create table cart (
  cart_id smallserial primary key,
  chatbot_id uuid not null references chatbot(chatbot_id),
  user_id varchar(20) not null references users(user_id) on update cascade,
  create_at timestamp with time zone not null default now(),
  unique (user_id, chatbot_id)
);

create table favorite_bot (
  favorite_bot_id smallserial primary key,
  chatbot_id uuid not null references chatbot(chatbot_id),
  user_id varchar(20) not null references users(user_id) on update cascade,
  create_at timestamp with time zone not null default now(),
  unique (user_id, chatbot_id)
);
