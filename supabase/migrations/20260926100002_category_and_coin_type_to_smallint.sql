-- category.category_id と coin_transaction_type.type_id を integer(serial) から
-- smallint(smallserial相当) に変更する。参照側の列も合わせて smallint にする。
--
-- 外部キー制約名は 20260918015035_category_and_coin_type_to_serial.sql で
-- 明示的に付けたものを前提にしている。

begin;

alter table chatbot drop constraint chatbot_category_id_fkey;
alter table coin_transaction drop constraint coin_transaction_type_id_fkey;

alter table category alter column category_id type smallint;
alter table chatbot alter column category_id type smallint;
alter sequence category_category_id_seq as smallint;

alter table coin_transaction_type alter column type_id type smallint;
alter table coin_transaction alter column type_id type smallint;
alter sequence coin_transaction_type_type_id_seq as smallint;

alter table chatbot
  add constraint chatbot_category_id_fkey
  foreign key (category_id) references category(category_id);

alter table coin_transaction
  add constraint coin_transaction_type_id_fkey
  foreign key (type_id) references coin_transaction_type(type_id);

commit;
