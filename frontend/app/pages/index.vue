<template>
  <div>
    <!-- ===== hero ===== -->
    <CommonPageContainer :padded="false" class="grid grid-cols-1 items-center gap-8 py-12 md:grid-cols-[3fr_2fr] md:py-16">
      <div>
        <!-- LP のヒーロー見出しだけは、ページ見出しのルール(text-2xl)より大きくする -->
        <h1 class="mb-4 text-4xl leading-tight font-bold text-slate-900 md:text-5xl">
          あなたのチャットボットを、<br />
          つくる。売る。買う。
        </h1>
        <p class="mb-6 text-lg leading-relaxed text-slate-600">
          手持ちのテキストやPDFをアップロードするだけで、<br>専用チャットボットが完成。そのまま自分で使うのも、<br>マーケットで他の人に届けるのも自由です。
        </p>
        <div class="mb-3 flex flex-wrap gap-4">
          <UButton to="/login?tab=register" size="lg">新規登録</UButton>
          <UButton to="/login" size="lg" variant="outline">ログイン</UButton>
        </div>
        <NuxtLink to="/main" class="inline-block text-sm text-primary hover:underline">
          → ゲストとしてマーケットを見る
        </NuxtLink>
      </div>
      <div class="flex aspect-[4/3] items-center justify-center bg-slate-200 p-6 text-center text-sm text-slate-600">
        チャットボット作成/マーケット画面のスクリーンショット
      </div>
    </CommonPageContainer>

    <!-- ===== how it works ===== -->
    <CommonPageContainer :padded="false" class="py-12 md:py-16">
      <section id="how">
        <CommonSectionTitle size="lg" class="mb-6">使い方は3ステップ</CommonSectionTitle>
        <div class="grid gap-5 md:grid-cols-3">
          <UCard v-for="step in steps" :key="step.label">
            <div class="text-xs font-bold tracking-wider text-primary">{{ step.label }}</div>
            <h3 class="mt-2 text-lg font-bold text-slate-900">{{ step.title }}</h3>
            <p class="mt-2 text-sm whitespace-pre-line text-slate-600">{{ step.description }}</p>
          </UCard>
        </div>
      </section>
    </CommonPageContainer>

    <!-- ===== CTA ===== -->
    <section class="mt-6 bg-slate-700 text-white">
      <CommonPageContainer :padded="false" class="flex flex-wrap items-center justify-between gap-6 py-12 md:py-16">
        <h2 class="text-2xl font-bold">まずはゲストとしてマーケットを見てみませんか？</h2>
        <UButton to="/main" size="lg">ゲストとしてマーケットを見る</UButton>
      </CommonPageContainer>
    </section>
  </div>
</template>

<script setup>
definePageMeta({
  layout: 'landing',
})

useHead({
  title: 'botttle | あなたのチャットボットを、つくる。売る。買う。',
})

const steps = [
  {
    label: 'STEP 01',
    title: 'テキスト・PDFをアップロード',
    description: 'FAQ、マニュアル、資料などをそのまま投入する\nだけ。前処理は不要です。',
  },
  {
    label: 'STEP 02',
    title: 'チャットボットが自動生成',
    description: '内容を理解した専用ボットが数分で完成。\nテスト会話ですぐ確認できます。',
  },
  {
    label: 'STEP 03',
    title: 'マーケットで売買・活用',
    description: '自分で使うも良し、マーケットに出品して\n他のユーザーに届けるも良し。',
  },
]
</script>
