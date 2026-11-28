-- =========================================================
-- RAG用チャンクテーブル
-- ローカル（e5: 384次元）と OpenAI（1536次元）の埋め込みを別の列に持つ
-- =========================================================

create extension if not exists vector;

create table if not exists public.bot_chunk (
    chunk_id          uuid primary key default gen_random_uuid(),
    chatbot_id        uuid not null
                      references public.chatbot (chatbot_id) on delete cascade,
    pdf_id            uuid not null
                      references public.bot_pdf (pdf_id) on delete cascade,
    chunk_index       integer not null,              -- ファイル内での順番
    page              integer,                       -- ページ番号（txt・文書情報は null）
    is_doc_info       boolean not null default false,-- 文書情報チャンクなら true
    content           text not null,                 -- チャンク本文
    embedding_local   vector(384),                   -- intfloat/multilingual-e5-small
    embedding_openai  vector(1536),                  -- text-embedding-3-small
    embedding_model   text not null,                 -- 作成に使ったモデル名（再取り込み判定用）
    created_at        timestamptz not null default now(),
    unique (pdf_id, chunk_index),
    check (embedding_local is not null or embedding_openai is not null)
);

-- ボット単位で絞り込むため
create index if not exists bot_chunk_chatbot_id_idx
    on public.bot_chunk (chatbot_id);

-- ベクトル検索用（コサイン距離）
create index if not exists bot_chunk_embedding_local_idx
    on public.bot_chunk using hnsw (embedding_local vector_cosine_ops);

create index if not exists bot_chunk_embedding_openai_idx
    on public.bot_chunk using hnsw (embedding_openai vector_cosine_ops);

-- バックエンド（secret キー）からだけ触る前提。ポリシーは作らない
alter table public.bot_chunk enable row level security;

-- =========================================================
-- 検索用の関数（retriever.py から rpc で呼ぶ）
-- =========================================================

create or replace function public.match_bot_chunks_local(
    p_chatbot_id    uuid,
    query_embedding vector(384),
    match_count     integer default 10
)
returns table (
    chunk_id    uuid,
    pdf_id      uuid,
    file_name   text,
    page        integer,
    chunk_index integer,
    is_doc_info boolean,
    content     text,
    similarity  double precision
)
language sql stable
as $$
    select c.chunk_id, c.pdf_id, p.file_name, c.page, c.chunk_index,
           c.is_doc_info, c.content,
           1 - (c.embedding_local <=> query_embedding) as similarity
    from public.bot_chunk c
    join public.bot_pdf p on p.pdf_id = c.pdf_id
    where c.chatbot_id = p_chatbot_id
      and c.embedding_local is not null
    order by c.embedding_local <=> query_embedding
    limit match_count;
$$;

create or replace function public.match_bot_chunks_openai(
    p_chatbot_id    uuid,
    query_embedding vector(1536),
    match_count     integer default 10
)
returns table (
    chunk_id    uuid,
    pdf_id      uuid,
    file_name   text,
    page        integer,
    chunk_index integer,
    is_doc_info boolean,
    content     text,
    similarity  double precision
)
language sql stable
as $$
    select c.chunk_id, c.pdf_id, p.file_name, c.page, c.chunk_index,
           c.is_doc_info, c.content,
           1 - (c.embedding_openai <=> query_embedding) as similarity
    from public.bot_chunk c
    join public.bot_pdf p on p.pdf_id = c.pdf_id
    where c.chatbot_id = p_chatbot_id
      and c.embedding_openai is not null
    order by c.embedding_openai <=> query_embedding
    limit match_count;
$$;