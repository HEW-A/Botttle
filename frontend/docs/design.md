# デザインルール（frontend）

画面ごとに見た目がばらつかないよう、新しく書く画面・直す画面は次のルールに合わせてください。
設定の実体は `app/assets/css/main.css`（トークン）と `app/app.config.ts`（Nuxt UI のテーマ）にあります。

元になったデザイン案：Claude Design の「botttle 角丸比較」キャンバスの案D

## 基本

| 項目 | ルール |
|---|---|
| フォント | M PLUS 1 Code（全体に指定済み。`font-[...]` は書かない） |
| ページ背景 | `slate-50`（body に指定済み） |
| メインカラー | `primary`（= blue-600）。`bg-primary` / `text-primary` / `bg-primary-50` などを使う |
| グレー | `slate` だけを使う（`gray` / `zinc` などは使わない） |
| 色の直書き | `#2563eb` のような hex は書かない |

## 角丸：原則なし

| 役割 | 角丸 | クラス | 対象 |
|---|---|---|---|
| 入れ物 | なし | （何も書かない） | カード、パネル、バッジ、情報バー、画像 |
| 操作する部品 | 6px | `rounded-control` | ボタン、入力欄 |
| 会話の中身 | 22px | `rounded-bubble` | チャットの吹き出し |
| 円形 | 丸 | `rounded-full` | アバター、ドット |

`rounded-md` / `rounded-lg` などは 0 になる設定なので、書いても効きません（書かないでください）。

## 文字

| 用途 | クラス |
|---|---|
| ページ見出し h1 | `text-2xl font-bold text-slate-900`（`CommonPageHeader` を使う） |
| セクション見出し h2 | `text-lg font-bold text-slate-900`（`CommonSectionTitle` を使う） |
| 本文 | `text-sm text-slate-700` |
| 補足・メタ情報 | `text-xs` または `text-sm` + `text-slate-500` |

`text-[13px]` のような任意の値は使わず、Tailwind の段階（`text-xs` / `text-sm` / `text-base` …）を使います。

## 部品

生の `<button>` や `<input>` にクラスを並べず、次の部品を使います。

| 用途 | 使うもの |
|---|---|
| ボタン | `UButton`（`size`: sm 32px / md 44px / lg 48px） |
| プライマリボタン | `<UButton>`（既定） |
| セカンダリボタン | `<UButton variant="outline">` |
| テキストボタン | `<UButton variant="ghost">` |
| 入力欄 | `UInput` / `UTextarea`（どちらも角丸 6px・文字 `text-sm`） |
| カード・パネル | `UCard`（`variant="outline"` が既定。白地 + slate-200 の枠） |
| ページの幅と余白 | `CommonPageContainer`（フォーム画面は `size="narrow"`） |
| ページ見出し | `CommonPageHeader`（`title` / `description` / `#actions`） |
| セクション見出し | `CommonSectionTitle` |
| チャットの吹き出し | `CommonChatBubble`（`sender="user" \| "bot"`、`avatar` に 1 文字） |
| 入力中の表示 | `CommonTypingIndicator` |

ボタンは上の3種類（`primary` の solid / outline / ghost）を使います。無効時（`disabled`）のグレー表示はこの3種類にだけ設定しています。
それ以外の色・variant（`color="error"` や `variant="soft"` など）は Nuxt UI 標準の「少し薄くなる」表示になるので、使う場合は無効時の見た目を確認してください。

## レイアウト

| レイアウト | 使う画面 |
|---|---|
| `default` | 通常の画面（ヘッダー・フッター付き）。ページ側でヘッダー・フッター・背景色を書かない |
| `auth` | ログイン・新規登録（ヘッダーなし、中央寄せ）。`definePageMeta({ layout: 'auth' })` |

`layout: false` にしてページ内で `CommonAppHeader` を書く作り方は、今後は使いません（既存の画面は順次移行します）。

## ページのひな形

```vue
<template>
  <CommonPageContainer>
    <CommonPageHeader title="カート" description="ご注文内容をご確認ください。" />

    <UCard>
      <CommonSectionTitle>ご注文商品</CommonSectionTitle>
      <!-- 中身 -->
      <UButton block size="lg">購入を確定する</UButton>
    </UCard>
  </CommonPageContainer>
</template>
```
