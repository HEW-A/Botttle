<template>
  <div class="flex min-h-screen flex-col font-['M_PLUS_1_Code']">
    <header class="flex flex-wrap items-center justify-between gap-3 px-6 py-4">
      <span class="text-2xl tracking-wide">botttle</span>
      <nav class="flex flex-wrap items-center gap-3 md:gap-5">
        <a href="#how" class="text-sm whitespace-nowrap hover:text-blue-600">使い方</a>
        <NuxtLink
          to="/main"
          class="inline-flex items-center whitespace-nowrap rounded-md border border-gray-200 px-4 py-2 text-sm font-medium hover:bg-gray-50"
        >
          ゲストでマーケットを見る
        </NuxtLink>
        <NuxtLink
          to="/login"
          class="inline-flex items-center whitespace-nowrap rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          ログイン
        </NuxtLink>
      </nav>
    </header>

    <main class="flex-1">
      <section class="mx-auto grid max-w-6xl grid-cols-1 items-center gap-8 px-6 py-12 md:grid-cols-2 md:py-16">
        <div>
          <span class="mb-4 inline-block rounded bg-blue-100 px-3 py-1 text-xs text-blue-700">
            テキスト・PDFからボットが作れる、CtoCマーケット
          </span>
          <h1 class="my-4 text-4xl font-semibold leading-tight md:text-5xl">
            あなたのチャットボットを、<br />
            つくる。売る。買う。
          </h1>
          <p class="mb-6 max-w-md text-lg leading-relaxed text-gray-600">
            手持ちのテキストやPDFをアップロードするだけで、専用チャットボットが完成。そのまま自分で使うのも、マーケットで他の人に届けるのも自由です。
          </p>
          <div class="mb-6 flex flex-wrap gap-4">
            <NuxtLink
              to="/login"
              class="inline-flex items-center rounded-md bg-blue-600 px-6 py-3 text-base font-medium text-white hover:bg-blue-700"
            >
              ログインして始める
            </NuxtLink>
            <NuxtLink
              to="/main"
              class="inline-flex items-center rounded-md border border-gray-200 px-6 py-3 text-base font-medium hover:bg-gray-50"
            >
              ゲストとしてマーケットを見る
            </NuxtLink>
          </div>
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
            <p class="mt-2 text-sm text-gray-600">FAQ、マニュアル、資料などをそのまま投入するだけ。前処理は不要です。</p>
          </div>
          <div class="rounded border border-gray-200 p-4 shadow-sm">
            <div class="text-xs font-semibold tracking-wider text-blue-600">STEP 02</div>
            <div class="mt-2 text-lg font-semibold">チャットボットが自動生成</div>
            <p class="mt-2 text-sm text-gray-600">内容を理解した専用ボットが数分で完成。テスト会話ですぐ確認できます。</p>
          </div>
          <div class="rounded border border-gray-200 p-4 shadow-sm">
            <div class="text-xs font-semibold tracking-wider text-blue-600">STEP 03</div>
            <div class="mt-2 text-lg font-semibold">マーケットで売買・活用</div>
            <p class="mt-2 text-sm text-gray-600">自分で使うも良し、マーケットに出品して他のユーザーに届けるも良し。</p>
          </div>
        </div>
      </section>

      <section class="mt-6 bg-slate-700 px-6 py-12 text-white md:py-16">
        <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-6">
          <h2 class="text-2xl font-semibold">まずはゲストでマーケットを覗いてみませんか？</h2>
          <div class="flex flex-wrap gap-4">
            <NuxtLink
              to="/main"
              class="inline-flex items-center rounded-md border border-white px-4 py-2 text-sm font-medium text-white hover:bg-white/10"
            >
              ゲストとしてマーケットを見る
            </NuxtLink>
            <NuxtLink
              to="/login"
              class="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              ログイン
            </NuxtLink>
          </div>
        </div>
      </section>
    </main>

    <footer class="border-t border-gray-200 px-6 py-6 text-center text-sm text-gray-400">© 2026 botttle</footer>
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
