-- users の主キーを id(uuid) から user_id(varchar(20)) に変更し、id 列は削除する。
--
-- users.id を参照していた下記の列を、users.user_id を参照する varchar(20) に置き換える。
--   chatbot.creator_id
--   purchases.buyer_id
--   conversations.user_id
--   coin_transaction.user_id
--   bot_arena.voter_id
-- 既存データは users.id -> users.user_id の対応で変換するので、
-- データが入っていても入っていなくても実行できる。
--
-- 外部キーには on update cascade を付け、user_id を変更した場合も参照側が追随するようにする。
--
-- 旧列を drop column すると、その列に付いていた外部キー制約も自動で消えるため、
-- 制約名（デフォルト命名かどうか）には依存しない。
--
-- 実行前の注意:
--   user_id が重複していると主キーを付けられず失敗する（トランザクションごと取り消される）。
--   事前に下記で重複が無いことを確認すること。
--     select user_id, count(*) from users group by user_id having count(*) > 1;
--   また、users.id を参照する RLS ポリシー・ビュー・関数を Supabase 上で作成している場合は
--   id 列の削除が失敗するので、先にそれらを削除・修正すること。

begin;

-- ============================================================
-- 参照側に user_id(varchar) の新しい列を作り、既存データを変換して入れる
-- ============================================================

alter table chatbot add column creator_id_new varchar(20);
update chatbot t set creator_id_new = u.user_id from users u where t.creator_id = u.id;

alter table purchases add column buyer_id_new varchar(20);
update purchases t set buyer_id_new = u.user_id from users u where t.buyer_id = u.id;

alter table conversations add column user_id_new varchar(20);
update conversations t set user_id_new = u.user_id from users u where t.user_id = u.id;

alter table coin_transaction add column user_id_new varchar(20);
update coin_transaction t set user_id_new = u.user_id from users u where t.user_id = u.id;

alter table bot_arena add column voter_id_new varchar(20);
update bot_arena t set voter_id_new = u.user_id from users u where t.voter_id = u.id;

-- ============================================================
-- 旧列（uuid）を削除して、新しい列に置き換える
-- ============================================================

alter table chatbot drop column creator_id;
alter table chatbot rename column creator_id_new to creator_id;
alter table chatbot alter column creator_id set not null;

alter table purchases drop column buyer_id;
alter table purchases rename column buyer_id_new to buyer_id;
alter table purchases alter column buyer_id set not null;

alter table conversations drop column user_id;
alter table conversations rename column user_id_new to user_id;
alter table conversations alter column user_id set not null;

alter table coin_transaction drop column user_id;
alter table coin_transaction rename column user_id_new to user_id;
alter table coin_transaction alter column user_id set not null;

alter table bot_arena drop column voter_id;
alter table bot_arena rename column voter_id_new to voter_id;
alter table bot_arena alter column voter_id set not null;

-- ============================================================
-- users の主キーを付け替える（id 列ごと users_pkey も消える）
-- ============================================================

alter table users drop column id;

alter table users add primary key (user_id);

-- ============================================================
-- 参照側に外部キーを付け直す
-- ============================================================

alter table chatbot
  add constraint chatbot_creator_id_fkey
  foreign key (creator_id) references users(user_id) on update cascade;

alter table purchases
  add constraint purchases_buyer_id_fkey
  foreign key (buyer_id) references users(user_id) on update cascade;

alter table conversations
  add constraint conversations_user_id_fkey
  foreign key (user_id) references users(user_id) on update cascade;

alter table coin_transaction
  add constraint coin_transaction_user_id_fkey
  foreign key (user_id) references users(user_id) on update cascade;

alter table bot_arena
  add constraint bot_arena_voter_id_fkey
  foreign key (voter_id) references users(user_id) on update cascade;

commit;
