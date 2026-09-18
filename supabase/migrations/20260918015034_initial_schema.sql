-- 現在Supabase上に存在するスキーマをそのままベースラインとして記録したもの。
-- ここから先のスキーマ変更は、このファイルを直接書き換えるのではなく
-- 新しいマイグレーションファイルを追加して ALTER していくこと。

create extension if not exists pgcrypto;

create type sale_status_enum as enum ('unlisted', 'listed', 'sold');
create type message_role_enum as enum ('user', 'ai');

create table users (
  id uuid primary key default gen_random_uuid(),
  user_id varchar(20) not null,
  username varchar(20) not null unique,
  user_mailaddless text,
  auth_email text not null,
  supabase_uid uuid not null unique,
  user_rank integer,
  profile_image_url text,
  developer_profile text,
  rating_avg numeric(2,1),
  create_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now()
);

create table category (
  category_id uuid primary key default gen_random_uuid(),
  category_name text not null
);

create table chatbot (
  chatbot_id uuid primary key default gen_random_uuid(),
  bot_name varchar(40) not null,
  creator_id uuid not null references users(id),
  price integer,
  description text,
  category_id uuid references category(category_id),
  thumbnail_url text,
  sale_status sale_status_enum not null,
  create_at timestamp with time zone not null default now(),
  update_at timestamp with time zone not null default now()
);

create table purchases (
  purchase_id uuid primary key default gen_random_uuid(),
  chatbot_id uuid not null references chatbot(chatbot_id),
  buyer_id uuid not null references users(id),
  rating integer,
  comment text,
  payment_method text not null,
  purchsed_at timestamp with time zone not null default now(),
  update_at timestamp with time zone not null default now()
);

create table bot_pdf (
  pdf_id uuid primary key default gen_random_uuid(),
  chatbot_id uuid not null references chatbot(chatbot_id),
  file_path text not null,
  file_name text not null,
  extracted_text text not null,
  uploaded_at timestamp with time zone not null default now()
);

create table conversations (
  conversation_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  chatbot_id uuid not null references chatbot(chatbot_id),
  created_at timestamp with time zone not null default now()
);

create table messages (
  message_id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(conversation_id),
  role message_role_enum not null,
  content text not null,
  created_at timestamp with time zone not null default now()
);

create table coin_transaction_type (
  type_id uuid primary key default gen_random_uuid(),
  type_name text not null
);

create table coin_transaction (
  coin_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id),
  amount integer not null,
  type_id uuid not null references coin_transaction_type(type_id),
  related_id uuid,
  created_at timestamp with time zone not null default now()
);

create table bot_arena (
  arena_id uuid primary key default gen_random_uuid(),
  bot_a_id uuid not null references chatbot(chatbot_id),
  bot_b_id uuid not null references chatbot(chatbot_id),
  bot_winner_id uuid not null references chatbot(chatbot_id),
  voter_id uuid not null references users(id),
  created_at timestamp with time zone not null default now()
);

insert into coin_transaction_type (type_name) values
  ('purchase'),
  ('reward'),
  ('charge'),
  ('refund');
