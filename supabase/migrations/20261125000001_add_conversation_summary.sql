-- RAG チャットの会話履歴の要約を保存する
-- summary          : 古い会話を要約した文章（backend/rag/history.py が更新する）
-- summarized_until : この日時までのメッセージは summary に含まれている

alter table conversations
  add column summary text,
  add column summarized_until timestamp with time zone;

-- 会話ごとにメッセージを時系列で読むための索引
create index if not exists messages_conversation_id_created_at_idx
  on messages (conversation_id, created_at);

-- ユーザーがボットごとの会話一覧を開くための索引
create index if not exists conversations_user_id_chatbot_id_idx
  on conversations (user_id, chatbot_id, created_at desc);
