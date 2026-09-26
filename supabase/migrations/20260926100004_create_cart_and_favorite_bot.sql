-- カート機能用の cart、お気に入り機能用の favorite_bot を追加する。
--
-- 同じユーザーが同じチャットボットを二重にカート・お気に入りに入れられないよう
-- (user_id, chatbot_id) に UNIQUE 制約を付ける。
--
-- 主キーは serial(integer) にする。
--   smallserial だと採番できるのが 32767 までで、行を削除しても番号は
--   再利用されないため、カートの出し入れやお気に入りの付け外しで上限に達しやすい。

create table cart (
  cart_id serial primary key,
  chatbot_id uuid not null references chatbot(chatbot_id),
  user_id varchar(20) not null references users(user_id) on update cascade,
  create_at timestamp with time zone not null default now(),
  unique (user_id, chatbot_id)
);

create table favorite_bot (
  favorite_bot_id serial primary key,
  chatbot_id uuid not null references chatbot(chatbot_id),
  user_id varchar(20) not null references users(user_id) on update cascade,
  create_at timestamp with time zone not null default now(),
  unique (user_id, chatbot_id)
);
