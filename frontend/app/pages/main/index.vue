<template>
  <div class="bg-white font-['M_PLUS_1_Code'] text-gray-900">
    <!-- ===== hero ===== -->
    <section class="mx-auto max-w-6xl px-8 pb-6 pt-10" />

    <!-- ===== categories ===== -->
    <section id="categories" class="mx-auto max-w-6xl px-8 py-10">
      <h2 class="mb-6 text-2xl font-bold">カテゴリから探す</h2>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <div
          v-for="category in categories"
          :key="category.name"
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
            v-html="category.icon"
          />
          <h4 class="text-sm font-semibold">{{ category.name }}</h4>
          <span class="text-xs text-gray-500">{{ category.count }}点</span>
        </div>
      </div>
    </section>

    <!-- ===== featured listings ===== -->
    <section class="mx-auto max-w-6xl px-8 py-10">
      <div class="mb-5 flex items-baseline justify-between">
        <h2 class="text-2xl font-bold">注目のチャットボット</h2>
        <a href="#" class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:underline">
          もっと見る
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
        </a>
      </div>
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="listing in featuredListings" :key="listing.title" class="border border-gray-200">
          <div class="relative flex aspect-[4/3] items-center justify-center bg-gray-100 p-4 text-center text-xs text-gray-500">
            {{ listing.imageLabel }}
            <span
              v-if="listing.sold"
              class="absolute left-2 top-2 bg-gray-100 px-2.5 py-1 text-xs text-gray-800"
            >
              売り切れ
            </span>
          </div>
          <div class="flex flex-col gap-2 p-3.5">
            <span :class="tagClass(listing.tagVariant)">{{ listing.tag }}</span>
            <h4 class="text-base font-semibold">{{ listing.title }}</h4>
            <div class="flex items-center justify-between">
              <span class="text-lg font-bold">{{ listing.price }}</span>
              <span class="flex items-center gap-1.5 text-xs text-gray-500">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                {{ listing.rating }} ({{ listing.reviews }})
              </span>
            </div>
          </div>
        </div>
      </div>
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
      <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="listing in newListings" :key="listing.title" class="border border-gray-200">
          <div class="flex aspect-[4/3] items-center justify-center bg-gray-100 p-4 text-center text-xs text-gray-500">
            {{ listing.imageLabel }}
          </div>
          <div class="flex flex-col gap-2 p-3.5">
            <span :class="tagClass(listing.tagVariant)">{{ listing.tag }}</span>
            <h4 class="text-base font-semibold">{{ listing.title }}</h4>
            <span class="text-lg font-bold">{{ listing.price }}</span>
          </div>
        </div>
      </div>
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

const categories = [
  {
    name: 'カスタマーサポート型',
    count: '1,204',
    icon: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
  },
  {
    name: '予約・受付型',
    count: '856',
    icon: '<rect x="3" y="4" width="18" height="18" rx="0"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
  },
  {
    name: '多言語対応型',
    count: '642',
    icon: '<circle cx="12" cy="12" r="9"></circle><path d="M12 3a15 15 0 0 0 0 18M3 12h18"></path>',
  },
  {
    name: '学習・教育型',
    count: '530',
    icon: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
  },
  {
    name: 'マーケティング支援型',
    count: '478',
    icon: '<path d="M3 3v18h18"></path><path d="M7 15l4-4 3 3 5-6"></path>',
  },
  {
    name: 'エンタメ・雑談型',
    count: '391',
    icon: '<circle cx="12" cy="12" r="9"></circle><path d="M9 10h.01M15 10h.01M8 15c1 1.2 2.4 2 4 2s3-.8 4-2"></path>',
  },
]

const tagClass = (variant) => {
  const base = 'inline-flex w-fit items-center px-2.5 py-1 text-[11px]'
  const variants = {
    accent: 'bg-blue-100 text-blue-800',
    'accent-2': 'bg-slate-100 text-slate-800',
    outline: 'border border-blue-600 text-blue-600',
  }
  return `${base} ${variants[variant]}`
}

const featuredListings = [
  {
    tag: 'カスタマーサポート',
    tagVariant: 'accent',
    title: 'FAQ自動応答ボット「サポやん」',
    imageLabel: 'FAQ自動応答ボットの画像',
    price: '¥12,000',
    rating: '4.8',
    reviews: 32,
    sold: false,
  },
  {
    tag: '予約受付',
    tagVariant: 'accent-2',
    title: '美容室向け予約ボット「よやくん」',
    imageLabel: '予約受付ボットの画像',
    price: '¥28,000',
    rating: '4.9',
    reviews: 18,
    sold: false,
  },
  {
    tag: '多言語対応',
    tagVariant: 'outline',
    title: '越境EC向け接客ボット「Global-chat」',
    imageLabel: '多言語対応ボットの画像',
    price: '¥45,000',
    rating: '4.7',
    reviews: 9,
    sold: false,
  },
  {
    tag: '学習支援',
    tagVariant: 'accent',
    title: '英会話練習ボット「Talky」',
    imageLabel: '学習支援ボットの画像',
    price: '¥8,000',
    rating: '4.6',
    reviews: 41,
    sold: true,
  },
]

const newListings = [
  {
    tag: 'マーケティング',
    tagVariant: 'accent-2',
    title: 'SNS運用アシスト「PostBuddy」',
    imageLabel: 'マーケティング支援ボットの画像',
    price: '¥19,800',
  },
  {
    tag: 'エンタメ',
    tagVariant: 'accent',
    title: '雑談相手ボット「おしゃべりモモ」',
    imageLabel: 'エンタメボットの画像',
    price: '¥3,500',
  },
  {
    tag: 'カスタマーサポート',
    tagVariant: 'outline',
    title: '返品対応自動化ボット「Returnie」',
    imageLabel: 'カスタマーサポートボットの画像',
    price: '¥33,000',
  },
  {
    tag: '予約受付',
    tagVariant: 'accent-2',
    title: 'クリニック受付ボット「Carely」',
    imageLabel: '予約受付ボットの画像',
    price: '¥52,000',
  },
]

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
