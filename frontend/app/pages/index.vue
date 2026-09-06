<template>
  <div class="flex min-h-screen flex-col font-['M_PLUS_1_Code']">
    <CommonAppHeader force-guest hide-search hide-ranking />

    <main class="flex-1">
      <section
        class="mx-auto grid max-w-6xl grid-cols-1 items-center gap-8 px-6 py-12 md:grid-cols-[3fr_2fr] md:py-16"
      >
        <div>
          <span class="mb-4 inline-block rounded bg-blue-100 px-3 py-1 text-xs text-blue-700">
            テキスト・PDFからボットが作れる、CtoCマーケット
          </span>
          <h1 class="my-4 text-4xl font-semibold leading-tight md:text-5xl">
            あなたのチャットボットを、<br />
            つくる。売る。買う。
          </h1>
          <p class="mb-6 text-lg leading-relaxed text-gray-600">
            手持ちのテキストやPDFをアップロードするだけで、<br>専用チャットボットが完成。そのまま自分で使うのも、<br>マーケットで他の人に届けるのも自由です。
          </p>
          <div class="mb-3 flex flex-wrap gap-4">
            <CommonAppButton to="/login?tab=register" variant="primary" size="lg">新規登録</CommonAppButton>
            <CommonAppButton to="/login" variant="outline" size="lg">ログイン</CommonAppButton>
          </div>
          <NuxtLink to="/main" class="mb-6 inline-block text-sm text-blue-600 hover:underline">
            → ゲストとしてマーケットを見る
          </NuxtLink>
          <div class="flex flex-wrap gap-3">
            <span class="rounded border border-blue-600 px-3 py-1 text-xs text-blue-600">テキスト/PDF読込</span>
            <span class="rounded border border-blue-600 px-3 py-1 text-xs text-blue-600">ボットの売買</span>
            <span class="rounded border border-blue-600 px-3 py-1 text-xs text-blue-600">個人クリエイター歓迎</span>
          </div>
        </div>
        <div
          class="flex aspect-[4/3] items-center justify-center rounded border border-gray-200 bg-gray-100 p-6 text-center text-sm text-gray-600"
        >
          チャットボット作成/マーケット画面のスクリーンショット
        </div>
      </section>

      <section id="how" class="mx-auto max-w-6xl px-6 py-12 md:py-16">
        <div class="mb-6">
          <span class="rounded bg-gray-100 px-3 py-1 text-xs text-gray-700">HOW IT WORKS</span>
          <h2 class="mt-3 text-3xl font-semibold">使い方は3ステップ</h2>
        </div>
        <div class="grid gap-5 md:grid-cols-3">
          <div class="rounded border border-gray-200 p-4 shadow-sm">
            <div class="text-xs font-semibold tracking-wider text-blue-600">STEP 01</div>
            <div class="mt-2 text-lg font-semibold">テキスト・PDFをアップロード</div>
            <p class="mt-2 text-sm text-gray-600">FAQ、マニュアル、資料などをそのまま投入する<br>だけ。前処理は不要です。</p>
          </div>
          <div class="rounded border border-gray-200 p-4 shadow-sm">
            <div class="text-xs font-semibold tracking-wider text-blue-600">STEP 02</div>
            <div class="mt-2 text-lg font-semibold">チャットボットが自動生成</div>
            <p class="mt-2 text-sm text-gray-600">内容を理解した専用ボットが数分で完成。<br>テスト会話ですぐ確認できます。</p>
          </div>
          <div class="rounded border border-gray-200 p-4 shadow-sm">
            <div class="text-xs font-semibold tracking-wider text-blue-600">STEP 03</div>
            <div class="mt-2 text-lg font-semibold">マーケットで売買・活用</div>
            <p class="mt-2 text-sm text-gray-600">自分で使うも良し、マーケットに出品して<br>他のユーザーに届けるも良し。</p>
          </div>
        </div>
      </section>

      <section class="mt-6 bg-slate-700 px-6 py-12 text-white md:py-16">
        <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6">
          <h2 class="text-2xl font-semibold">まずはゲストとしてマーケットを見てみませんか？</h2>
          <CommonAppButton to="/main" variant="outline-white">ゲストとしてマーケットを見る</CommonAppButton>
        </div>
      </section>
    </main>

    <CommonAppFooter />
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

useHead({
  title: 'botttle | あなたのチャットボットを、つくる。売る。買う。',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})
</script>
