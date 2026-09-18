-- category.category_id と coin_transaction_type.type_id を
-- uuid から連番(serial)に変更する。
--
-- 対象を category / coin_transaction_type に絞った理由:
--   どちらも運営側が管理する固定的な小さいマスタテーブルで、
--   外部（フロントのURLやAPIレスポンス）に単体でIDが露出して
--   困る性質のものではないため。
--
-- リレーション（どのテーブルがどのテーブルを参照するか）自体は変更せず、
-- 参照先キーの型だけを uuid -> integer に変える。
-- 既存データがあっても、UUID -> 連番の対応関係を保ったまま
-- 参照側（chatbot.category_id / coin_transaction.type_id）を
-- 追随させるので、データが入っていても入っていなくても実行できる。
--
-- 実行前の注意:
--   制約名は元のCREATE TABLE文で明示的に付けていなかったため、
--   Postgresのデフォルト命名規則（<table>_<column>_fkey / <table>_pkey）を
--   前提にしている。実際の環境で制約名が異なる場合は、
--   下記のいずれかで事前に確認してから合わせて書き換えること。
--     select conname from pg_constraint where conrelid = 'chatbot'::regclass;
--     select conname from pg_constraint where conrelid = 'category'::regclass;
--     select conname from pg_constraint where conrelid = 'coin_transaction'::regclass;
--     select conname from pg_constraint where conrelid = 'coin_transaction_type'::regclass;

begin;

-- ============================================================
-- category.category_id: uuid -> serial(integer)
-- ============================================================

alter table category
  add column category_id_new serial;

alter table chatbot
  add column category_id_new integer;

update chatbot c
set category_id_new = cat.category_id_new
from category cat
where c.category_id = cat.category_id;

alter table chatbot
  drop constraint chatbot_category_id_fkey;

alter table category
  drop constraint category_pkey;

alter table category
  drop column category_id;

alter table category
  rename column category_id_new to category_id;

alter table category
  add primary key (category_id);

alter table chatbot
  drop column category_id;

alter table chatbot
  rename column category_id_new to category_id;

alter table chatbot
  add constraint chatbot_category_id_fkey
  foreign key (category_id) references category(category_id);

-- ============================================================
-- coin_transaction_type.type_id: uuid -> serial(integer)
-- ============================================================

alter table coin_transaction_type
  add column type_id_new serial;

alter table coin_transaction
  add column type_id_new integer;

update coin_transaction ct
set type_id_new = ctt.type_id_new
from coin_transaction_type ctt
where ct.type_id = ctt.type_id;

alter table coin_transaction
  drop constraint coin_transaction_type_id_fkey;

alter table coin_transaction_type
  drop constraint coin_transaction_type_pkey;

alter table coin_transaction_type
  drop column type_id;

alter table coin_transaction_type
  rename column type_id_new to type_id;

alter table coin_transaction_type
  add primary key (type_id);

alter table coin_transaction
  drop column type_id;

alter table coin_transaction
  rename column type_id_new to type_id;

alter table coin_transaction
  alter column type_id set not null;

alter table coin_transaction
  add constraint coin_transaction_type_id_fkey
  foreign key (type_id) references coin_transaction_type(type_id);

-- serial列作成時にシーケンス名が "..._new_seq" のままになるので、見た目を整える
alter sequence category_category_id_new_seq
  rename to category_category_id_seq;

alter sequence coin_transaction_type_type_id_new_seq
  rename to coin_transaction_type_type_id_seq;

commit;
