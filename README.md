# Botttle

Python(Flask) + Nuxt4 で構成する CtoC マーケット風 Web アプリケーション。

## 全体構成

```
project-root/
├── backend/    # Flask アプリケーション
└── frontend/   # Nuxt4 フロントエンド
```

## 起動確認手順（backend）

```bash
cd backend

# 初回のみ：仮想環境を作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate      # Windowsの場合: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 起動
python app.py
# → http://localhost:5000/api/health が {"status": "ok"} を返せばOK
# → http://localhost:5000/api/auth/health なども {"status": "ok", "domain": "auth"} を返す

# 作業終了時は仮想環境を抜ける
deactivate
```

### 各ドメインの疎通確認エンドポイント

| ドメイン       | エンドポイント                       |
| -------------- | ------------------------------------ |
| auth           | `GET /api/auth/health`               |
| bot_creation   | `GET /api/bots/health`               |
| botarena       | `GET /api/botarena/health`           |
| users          | `GET /api/users/health`              |
| common         | `GET /api/common/health`             |

## 起動確認手順（frontend）

```bash
cd frontend

# 依存関係のインストール
npm install

# 起動
npm run dev
# → http://localhost:3000 にアクセスすると "Backend status: ok" が表示されればOK
#   （backend が未起動の場合は "接続失敗" と表示される）
```

frontend は `runtimeConfig.public.apiBase`（デフォルト `http://localhost:5000`）を通じて backend の
`GET /api/health` を呼び出します。接続先を変更したい場合は環境変数で上書きできます。

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

## テスト実行

```bash
# backend側のテスト実行
cd backend
source .venv/bin/activate      # Windowsの場合: .venv\Scripts\activate
pytest

# frontend側のテスト実行
cd frontend
npm run test
```

## 備考

- `backend/` の各ドメインフォルダにある `test.py` は Blueprint 登録パターンを示すサンプルです。
  実際の開発では `routes.py` 等に置き換えて実装していく想定です。
- `frontend/app/pages/` 配下には疎通確認用の最小限の `index.vue` を配置しています。
