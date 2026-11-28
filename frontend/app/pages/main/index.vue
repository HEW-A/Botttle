<template>
  <div class="bg-white font-['M_PLUS_1_Code'] text-gray-900">
    <!-- ===== hero ===== -->
    <section class="mx-auto max-w-6xl px-8 pb-6 pt-10" />

    <!-- ===== categories ===== -->
    <section id="categories" class="mx-auto max-w-6xl px-8 py-10">
      <h2 class="mb-6 text-2xl font-bold">カテゴリから探す</h2>
      <div v-if="categoriesStatus === 'pending' && categories.length === 0" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div v-for="n in 6" :key="n" class="h-[126px] animate-pulse border border-gray-200 bg-gray-100" />
      </div>
      <p v-else-if="categoriesError" class="border border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
        カテゴリを読み込めませんでした。時間をおいて再度お試しください。
      </p>
      <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <!-- TODO: カテゴリで絞り込んだ商品一覧ページができたら、そこへのリンクにする -->
        <div
          v-for="category in categories"
          :key="category.category_id"
          class="flex cursor-pointer flex-col items-center gap-2.5 border border-gray-200 px-3 py-7 text-center hover:border-blue-600"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#1d4ed8"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
            v-html="categoryIcon(category.category_id)"
          />
          <h4 class="text-sm font-semibold">{{ category.category_name }}</h4>
          <span class="text-xs text-gray-500">{{ category.product_count.toLocaleString('ja-JP') }}点</span>
        </div>
      </div>
    </section>

    <!-- ===== featured listings ===== -->
    <!-- 商品が新着の4件分しか無いときは、注目に出す商品が無いのでセクションごと隠す -->
    <section v-if="showFeatured" class="mx-auto max-w-6xl px-8 py-10">
      <div class="mb-5 flex items-baseline justify-between">
        <h2 class="text-2xl font-bold">注目のチャットボット</h2>
        <a href="#" class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:underline">
          もっと見る
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </a>
      </div>
      <ProductCardGrid :products="featuredProducts" :status="featuredStatus" :error="featuredError" />
    </section>

    <!-- ===== new arrivals ===== -->
    <section class="mx-auto max-w-6xl px-8 py-10">
      <div class="mb-5 flex items-baseline justify-between">
        <h2 class="text-2xl font-bold">新着出品</h2>
        <a href="#" class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:underline">
          もっと見る
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </a>
      </div>
      <ProductCardGrid :products="newProducts" :status="newStatus" :error="newError" />
    </section>

    <!-- ===== how it works ===== -->
    <section id="how" class="mx-auto max-w-6xl px-8 py-14">
      <h2 class="mb-8 text-center text-2xl font-bold">かんたん3ステップ</h2>
      <div class="grid grid-cols-1 gap-8 md:grid-cols-3">
        <div v-for="step in steps" :key="step.title" class="px-3 text-center">
          <div
            class="mx-auto mb-4 flex h-14 w-14 items-center justify-center border border-gray-200 text-blue-700"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" v-html="step.icon" />
          </div>
          <h4 class="mb-2 font-semibold">{{ step.title }}</h4>
          <p class="mx-auto max-w-[32ch] text-sm text-gray-500">{{ step.description }}</p>
        </div>
      </div>
    </section>

    <!-- ===== trust ===== -->
    <section class="bg-gray-100 px-8 py-9">
      <div class="mx-auto flex max-w-6xl flex-wrap justify-between gap-6">
        <div v-for="trust in trustPoints" :key="trust.text" class="flex items-center gap-3">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" v-html="trust.icon" />
          <span class="text-sm">{{ trust.text }}</span>
        </div>
      </div>
    </section>

    <!-- ===== CTA ===== -->
    <section class="mx-auto my-14 max-w-6xl px-8">
      <div class="flex flex-col items-center gap-4 border border-gray-200 px-8 py-14 text-center">
        <h3 class="text-xl font-bold">あなたのボットも、出品してみませんか？</h3>
        <p class="mx-auto max-w-[48ch] text-gray-600">
          使わなくなった業務効率化ボットも、趣味で作った雑談ボットも。誰かにとって価値があるかもしれません。
        </p>
        <button
          type="button"
          class="inline-flex items-center bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
        >
          出品をはじめる
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
useHead({
  title: 'BOTMARKET | チャットボットCtoCマーケット',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

// 商品・カテゴリはAPIから取得する(3つを並行して取得し、SSRで描画してから返す)
const [
  { data: categories, status: categoriesStatus, error: categoriesError },
  { data: newProducts, status: newStatus, error: newError },
  { data: featuredProducts, status: featuredStatus, error: featuredError },
] = await Promise.all([
  useCategories(),
  useProductList({ limit: 4 }),
  // TODO: 注目の基準(評価・販売数など)が決まるまでは、新着の次の4件を表示する
  useProductList({ limit: 4, offset: 4 }),
])

// 注目は、読み込み中・取得失敗のときは枠を出し、取得できて0件のときだけ隠す
const showFeatured = computed(() => featuredStatus.value !== 'success' || featuredProducts.value.length > 0)

const steps = [
  {
    title: '1. 出品する',
    description: 'ボットの概要・利用シーン・価格を入力するだけで出品完了。',
    icon: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.29 7 12 12 20.71 7"></polyline><line x1="12" y1="22" x2="12" y2="12"></line>',
  },
  {
    title: '2. メッセージでやり取り',
    description: '気になる点は購入前にチャットで質問。安心して検討できます。',
    icon: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
  },
  {
    title: '3. 受け渡し・お支払い',
    description: '事務局を介した安心決済で、コードやアカウントを受け渡し。',
    icon: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="M9 12l2 2 4-4"></path>',
  },
]

const trustPoints = [
  {
    text: '本人確認済みユーザーのみ取引可能',
    icon: '<circle cx="9" cy="7" r="4"></circle><path d="M17 21v-2a4 4 0 0 0-3-3.87"></path><path d="M23 21v-2a4 4 0 0 0-3-3.85"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path><path d="M1 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"></path>',
  },
  {
    text: '事務局によるあんしんエスクロー決済',
    icon: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
  },
  {
    text: '受け渡し後もチャットでサポート',
    icon: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
  },
]
</script>
