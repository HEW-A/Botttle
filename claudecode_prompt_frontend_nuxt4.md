# ClaudeCodeに投げるプロンプト（フロントエンドNuxt4化）

既存のプロジェクトのfrontend部分を、Nuxt4の推奨ディレクトリ構成（`app/`ディレクトリ配下にpages/components等を集約するタイプ）に書き換えてもらう際に使うプロンプトです。backend側には触れません。

以下をそのままClaudeCodeに貼り付けてください。

---

frontendディレクトリの構成を、Nuxt4の推奨ディレクトリ構成に修正してください。現在Nuxt3的な構成（`pages/`や`components/`がfrontend直下に直接ある形）になっているものを、`app/`ディレクトリ配下に集約する形に書き換えてください。

**重要な制約**
- 実装（ページやコンポーネントの中身）は追加しないでください。今回もフォルダ構造の作成のみで、各フォルダ直下に `test.txt` を1つ置くだけにしてください（中身は空、もしくは1行コメントのみ）。
- backend側のフォルダ構成やファイルには一切手を加えないでください。

## frontendの新しいフォルダ構造

```
frontend/
├── app/
│   ├── app.vue
│   ├── pages/
│   │   ├── auth/
│   │   │   └── test.txt
│   │   ├── bots/
│   │   │   └── test.txt
│   │   ├── chat/
│   │   │   └── test.txt
│   │   └── mypage/
│   │       └── test.txt
│   ├── components/
│   │   ├── auth/
│   │   │   └── test.txt
│   │   ├── bot-creation/
│   │   │   └── test.txt
│   │   ├── botarena/
│   │   │   └── test.txt
│   │   ├── chat/
│   │   │   └── test.txt
│   │   └── common/
│   │       └── test.txt
│   ├── composables/
│   │   └── test.txt
│   ├── stores/
│   │   └── test.txt
│   ├── middleware/
│   │   └── test.txt
│   ├── plugins/
│   │   └── test.txt
│   └── utils/
│       └── test.txt
│
├── public/
│   └── test.txt
│
├── types/
│   └── test.txt
│
├── nuxt.config.ts
└── package.json
```

## 補足（Nuxt4構成のポイント）

- Nuxt4では `srcDir` が実質的に `app/` になり、`pages`, `components`, `composables`, `middleware`, `plugins`, `utils`, `app.vue` はすべて `app/` 配下に置く構成が標準になります
- `public/`（静的アセット）と `types/`（型定義）はプロジェクトルート直下（frontend直下）のままで問題ありません
- `nuxt.config.ts` には特別な設定は不要です（Nuxt4であれば標準でこの構成が既定になっているため、`srcDir`の明示指定も基本不要です）
- 既存のfrontend直下にある`pages/`, `components/`等が残っている場合は削除し、`app/`配下に作り直してください

---

**繰り返しになりますが、今回もフォルダ構造の作成のみで、各フォルダには `test.txt` を1つ置くだけにしてください。backend側には一切手を加えないでください。**
