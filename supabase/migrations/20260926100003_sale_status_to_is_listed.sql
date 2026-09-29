-- chatbot.sale_status(enum) を is_listed(boolean) に置き換える。
-- 1つのチャットボットを複数人が購入できる仕様のため「売り切れ(sold)」状態は不要になり、
-- 残る状態は「出品中 / 非出品」の2つだけなので boolean で表す。
--   true  : 出品中（旧 'listed'）
--   false : 非出品（旧 'unlisted'）
-- 既存データで 'sold' になっている行は、出品中として true にする。

begin;

alter table chatbot
  add column is_listed boolean not null default false;

update chatbot
set is_listed = (sale_status in ('listed', 'sold'));

alter table chatbot
  drop column sale_status;

drop type sale_status_enum;

commit;
