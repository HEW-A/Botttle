# ClaudeCodeに投げるプロンプト（backend: venv対応の追加）

既にbackendのフォルダ構造・`app.py`・各ドメインの`test.py`は作成済みという前提で、venv（Python仮想環境）に関する設定だけを追加するプロンプトです。

以下をそのままClaudeCodeに貼り付けてください。

---

backendディレクトリに対して、Python仮想環境（venv）を使った開発を前提としたセットアップ関連のファイルのみを追加してください。既存の `app.py` や各ドメインフォルダ内の `test.py` の中身は変更しないでください。

**やってほしいこと**

1. `backend/.gitignore` を作成し、以下を記載してください。
   ```
   .venv/
   __pycache__/
   *.pyc
   .env
   ```

2. プロジェクトルートまたは `backend/README.md` に、以下の起動手順を追記してください（既存の記述があれば、venvに関する記述だけを反映する形で修正してください）。

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

   # 作業終了時は仮想環境を抜ける
   deactivate
   ```

3. `backend/requirements.txt` がまだ無い、もしくは不足している場合のみ `flask`, `flask-cors` を追記してください（既にある場合は変更不要です）。

**やらないでほしいこと**
- 既存の `app.py` やBlueprintのコード内容を書き換えないでください。
- frontend側には一切手を加えないでください。
- 新しいビジネスロジックやエンドポイントを追加しないでください。

---

**繰り返しになりますが、今回の変更は `.gitignore` の作成とREADMEへの起動手順追記（+ 必要であれば`requirements.txt`の補完）のみです。それ以外のファイルは変更しないでください。**
