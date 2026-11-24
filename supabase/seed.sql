-- 開発用のダミーデータ（ホーム画面・商品詳細画面の表示確認用）
--
-- ローカル環境では `supabase db reset` で migrations の後に自動で流れる（config.toml の [db.seed]）。
-- 共有の Supabase に入れる場合は、SQL Editor にこのファイルの中身を貼り付けて実行する。
--
-- 何度流しても同じ結果になるよう、主キーを固定して on conflict do nothing にしている。
-- （既に同じIDの行がある場合は上書きせず、そのまま残す）
--
-- ここで作るユーザーは出品者として表示するためだけのもので、Supabase Auth のアカウントは無い
-- （ログインはできない）。メールアドレスは送信されない予約ドメイン example.com を使う。

begin;

-- ============================================================
-- カテゴリ（ホーム画面の「カテゴリから探す」の6つ）
-- ============================================================

insert into category (category_id, category_name) values
  (1, 'カスタマーサポート型'),
  (2, '予約・受付型'),
  (3, '多言語対応型'),
  (4, '学習・教育型'),
  (5, 'マーケティング支援型'),
  (6, 'エンタメ・雑談型')
on conflict (category_id) do nothing;

-- ID を固定して入れたので、次に採番される値が衝突しないよう連番を進めておく
select setval('category_category_id_seq', (select max(category_id) from category));

-- ============================================================
-- 出品者（ダミーユーザー）
-- ============================================================

insert into users (user_id, username, auth_email, supabase_uid, developer_profile, is_withdrawn, withdrawn_at) values
  ('dummy_seller01', 'sapo_lab',     'dummy_seller01@example.com', '10000000-0000-0000-0000-000000000001', 'カスタマーサポート向けのボットを中心に制作しています。', false, null),
  ('dummy_seller02', 'bot_kobo',     'dummy_seller02@example.com', '10000000-0000-0000-0000-000000000002', '予約・受付まわりの業務効率化ボットを作っています。',     false, null),
  ('dummy_seller03', 'lingo_works',  'dummy_seller03@example.com', '10000000-0000-0000-0000-000000000003', '多言語対応と学習支援のボットが得意です。',               false, null),
  -- 退会済みユーザー（この人の商品は一覧・詳細に出ないことの確認用）
  ('dummy_withdrawn', 'retired_dev', 'dummy_withdrawn@example.com', '10000000-0000-0000-0000-000000000004', null,                                                     true,  now() - interval '3 days')
on conflict (user_id) do nothing;

-- ============================================================
-- チャットボット（商品）
-- ============================================================
-- 一覧は create_at の新しい順に並ぶので、表示順が毎回同じになるよう日時をずらしている。
-- 00000000-0000-0000-0000-000000000001 は、商品詳細画面のモックで使っていたIDに合わせている。

insert into chatbot (chatbot_id, bot_name, creator_id, price, description, category_id, thumbnail_url, is_listed, create_at, update_at) values
  ('00000000-0000-0000-0000-000000000001', '対応品質評価AI「サポたん」', 'dummy_seller01', 48000,
   '問い合わせ内容を自動分類し、回答テンプレートを提案するカスタマーサポート特化型チャットボットです。既存のFAQデータを読み込ませるだけで、初回応答率と一次解決率の改善が見込めます。',
   1, null, true, now() - interval '10 days', now() - interval '10 days'),

  ('00000000-0000-0000-0000-000000000002', 'FAQ自動応答ボット「サポやん」', 'dummy_seller01', 12000,
   'よくある質問への回答を24時間自動で行うボットです。社内マニュアルのPDFを読み込ませるだけで使い始められます。',
   1, null, true, now() - interval '9 days', now() - interval '9 days'),

  ('00000000-0000-0000-0000-000000000003', '美容室向け予約ボット「よやくん」', 'dummy_seller02', 28000,
   '空き枠の案内から予約内容の確認まで、美容室の予約受付をチャットで完結させます。メニューや料金表の読み込みにも対応しています。',
   2, null, true, now() - interval '8 days', now() - interval '8 days'),

  ('00000000-0000-0000-0000-000000000004', '越境EC向け接客ボット「Global-chat」', 'dummy_seller03', 45000,
   '日本語・英語・中国語で商品案内や配送の質問に答える接客ボットです。商品カタログを読み込ませて使います。',
   3, null, true, now() - interval '7 days', now() - interval '7 days'),

  ('00000000-0000-0000-0000-000000000005', '英会話練習ボット「Talky」', 'dummy_seller03', 8000,
   '日常会話のロールプレイで英語のスピーキング練習ができるボットです。間違いをやさしく指摘してくれます。',
   4, null, true, now() - interval '6 days', now() - interval '6 days'),

  ('00000000-0000-0000-0000-000000000006', 'SNS運用アシスト「PostBuddy」', 'dummy_seller02', 19800,
   '投稿文の案出しやハッシュタグの提案など、SNS運用を手伝うボットです。過去の投稿を読み込ませると文体を合わせます。',
   5, null, true, now() - interval '5 days', now() - interval '5 days'),

  ('00000000-0000-0000-0000-000000000007', '雑談相手ボット「おしゃべりモモ」', 'dummy_seller01', 3500,
   'ちょっとした雑談や気分転換の相手になってくれるボットです。話題の振り方を設定で変えられます。',
   6, null, true, now() - interval '4 days', now() - interval '4 days'),

  ('00000000-0000-0000-0000-000000000008', '返品対応自動化ボット「Returnie」', 'dummy_seller01', 33000,
   '返品・交換の受付と、条件に応じた案内を自動化するボットです。返品ポリシーの文書を読み込ませて使います。',
   1, null, true, now() - interval '3 days', now() - interval '3 days'),

  ('00000000-0000-0000-0000-000000000009', 'クリニック受付ボット「Carely」', 'dummy_seller02', 52000,
   '診療時間の案内や予約の受付、来院前の問診をチャットで行うクリニック向けのボットです。',
   2, null, true, now() - interval '2 days', now() - interval '2 days'),

  ('00000000-0000-0000-0000-000000000010', '歴史学習ボット「レキシー」', 'dummy_seller03', 6000,
   '教科書の内容を読み込ませて、一問一答や時代の流れの解説ができる学習用ボットです。',
   4, null, true, now() - interval '1 day', now() - interval '1 day'),

  -- 非出品（一覧・詳細に出ないことの確認用）
  ('00000000-0000-0000-0000-000000000011', '下書き中のボット「テストくん」', 'dummy_seller02', 1000,
   'まだ出品していないボットです。',
   6, null, false, now() - interval '12 hours', now() - interval '12 hours'),

  -- 退会済みユーザーの出品（一覧・詳細に出ないことの確認用）
  ('00000000-0000-0000-0000-000000000012', '退会者のボット「のこりもの」', 'dummy_withdrawn', 2000,
   '退会済みユーザーが出品していたボットです。',
   5, null, true, now() - interval '6 hours', now() - interval '6 hours')
on conflict (chatbot_id) do nothing;

commit;
