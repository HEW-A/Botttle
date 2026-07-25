# ClaudeCodeに投げるプロンプト

以下をそのままClaudeCodeに貼り付けてください。

---

Python(Flask)とNuxt3で構成するCtoCマーケット風Webアプリケーションのプロジェクトについて、フォルダ構造を作成してください。

**重要な制約**
- frontend側はフォルダ構造の作成のみでよいです。各フォルダ直下に `test.txt` を1つ置くだけにしてください（中身は空、もしくは1行コメントのみ）。ページやコンポーネントの実装は不要です。
- backend側は各ドメインフォルダに `test.py` を置きますが、**中身は空にせず、Flaskの Blueprint 定義のサンプルコードを記載**してください（詳細は下記）。
- backendとフロントエンドの接続確認のため、`app.py` で全ドメインの Blueprint を登録し、`GET /api/health` で疎通確認できるようにしてください。

## 全体構成

```
project-root/
├── backend/
└── frontend/
```

## backendのフォルダ構造

```
backend/
├── app.py
├── requirements.txt
│
├── auth/
│   └── test.py
├── bot_creation/
│   └── test.py
├── botarena/
│   └── test.py
├── users/
│   └── test.py
└── common/
    └── test.py
```

### 各 `test.py` の中身（サンプル）

各ドメインフォルダの `test.py` には、そのドメイン名を使った Blueprint 定義の例を書いてください。中身はダミーの1エンドポイントのみで構いません。例えば `auth/test.py` は以下のようなイメージです。

```python
from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "auth"})
```

同様に `bot_creation/test.py`, `botarena/test.py`, `users/test.py`, `common/test.py` にも、それぞれのドメイン名を使ったBlueprintのサンプル（`bot_creation_bp`, `botarena_bp`, `users_bp`, `common_bp`）を用意してください。

### `app.py` の中身（サンプル）

`app.py` では、各ドメインの `test.py` からBlueprintをインポートし、登録する例を書いてください。イメージは以下の通りです。

```python
from flask import Flask
from flask_cors import CORS

from auth.test import auth_bp
from bot_creation.test import bot_creation_bp
from botarena.test import botarena_bp
from users.test import users_bp
from common.test import common_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(bot_creation_bp, url_prefix="/api/bots")
    app.register_blueprint(botarena_bp, url_prefix="/api/botarena")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(common_bp, url_prefix="/api/common")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
```

※ 実際に開発が始まったら、各メンバーが `test.py` の中身を `routes.py` 等に置き換えて実装していく想定です。あくまでBlueprintの登録パターンを示すサンプルとして扱ってください。

`requirements.txt` には `flask`, `flask-cors` のみ記載してください。

## frontendのフォルダ構造

各フォルダ直下に `test.txt` を1つ置くだけにしてください。

```
frontend/
├── pages/
│   ├── auth/
│   │   └── test.txt
│   ├── bots/
│   │   └── test.txt
│   ├── chat/
│   │   └── test.txt
│   └── mypage/
│       └── test.txt
├── components/
│   ├── auth/
│   │   └── test.txt
│   ├── bot-creation/
│   │   └── test.txt
│   ├── botarena/
│   │   └── test.txt
│   ├── chat/
│   │   └── test.txt
│   └── common/
│       └── test.txt
├── composables/
│   └── test.txt
├── stores/
│   └── test.txt
├── middleware/
│   └── test.txt
├── plugins/
│   └── test.txt
└── types/
    └── test.txt
```

## 起動確認手順（README等に記載してください）

```bash
cd backend
pip install -r requirements.txt
python app.py
# → http://localhost:5000/api/health が {"status": "ok"} を返せばOK
# → http://localhost:5000/api/auth/health なども {"status": "ok", "domain": "auth"} を返す
```

---

**繰り返しになりますが、frontend側はフォルダと `test.txt` のみで構いません。backend側は `app.py` でのBlueprint登録例と、各ドメインの `test.py` でのBlueprint定義例だけを実装し、それ以外のビジネスロジックは書かないでください。**
