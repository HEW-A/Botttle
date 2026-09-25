<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <div class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center gap-1.5 px-6 py-3 text-xs text-slate-500">
        <a href="#" class="text-slate-500 hover:text-blue-600">ホーム</a>
        <span>/</span>
        <a href="#" class="text-slate-500 hover:text-blue-600">チャットボット</a>
        <span>/</span>
        <a href="#" class="text-slate-500 hover:text-blue-600">{{ product.category }}</a>
        <span>/</span>
        <span class="text-slate-900">{{ product.name }}</span>
      </div>
    </div>

    <main class="flex-1">
      <div class="mx-auto max-w-6xl px-6 py-6">
        <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[0.85fr_1.5fr_0.85fr]">
          <!-- 試用チャット -->
          <section class="flex h-[calc(100vh-7rem)] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white lg:sticky lg:top-20">
            <div class="flex flex-col gap-2.5 border-b border-slate-200 px-5 py-4">
              <div>
                <h2 class="mb-1 text-[15px] font-bold text-slate-900">お試しチャット</h2>
                <p class="text-xs text-slate-500">1回の送信につき {{ product.costPerUse }}pt を消費します</p>
              </div>
              <div class="flex items-center justify-between rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5">
                <span class="text-[11.5px] text-blue-800">残り試用回数</span>
                <span class="text-[15px] font-bold whitespace-nowrap text-blue-700">{{ remainingTries }}回</span>
              </div>
            </div>

            <div class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 px-5 py-4">
              <div v-for="(msg, index) in messages" :key="index" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                <div
                  class="max-w-[75%] rounded-lg px-3.5 py-2.5 text-[13.5px] leading-relaxed"
                  :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'border border-slate-200 bg-white text-slate-900'"
                >
                  {{ msg.text }}
                </div>
              </div>
              <div v-if="isSending" class="flex justify-start">
                <div class="rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-[13px] text-slate-400">入力中…</div>
              </div>
            </div>

            <div class="border-t border-slate-200 px-5 py-3.5">
              <div v-if="hasTriesLeft" class="flex flex-col gap-2">
                <input
                  v-model="inputText"
                  type="text"
                  placeholder="質問を入力（例：営業時間を教えて）"
                  class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-[13.5px] text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
                  @keydown.enter="sendTrialMessage"
                />
                <button
                  type="button"
                  class="w-full rounded-lg border-2 border-transparent py-2.5 text-[13.5px] font-bold"
                  :class="sendDisabled ? 'cursor-not-allowed bg-slate-200 text-slate-400' : 'cursor-pointer bg-blue-600 text-white hover:bg-blue-700'"
                  :disabled="sendDisabled"
                  @click="sendTrialMessage"
                >
                  送信（{{ product.costPerUse }}pt）
                </button>
              </div>
              <div v-else class="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3.5">
                <span class="text-[13px] text-red-800">ポイント残高が不足しています。ポイントをチャージするとお試しを続けられます。</span>
                <button
                  type="button"
                  class="flex-none rounded-md bg-slate-700 px-4 py-2 text-[12.5px] font-bold whitespace-nowrap text-white hover:bg-slate-800"
                  @click="rechargePoints"
                >
                  ポイントをチャージ
                </button>
              </div>
            </div>
          </section>

          <!-- サムネイル・商品概要・レビュー -->
          <div class="flex min-w-0 flex-col gap-6">
            <div>
              <div class="relative flex aspect-video items-center justify-center overflow-hidden rounded-xl bg-slate-900">
                <div class="flex flex-col items-center gap-3 text-slate-300">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="1.5">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    <circle cx="9" cy="10" r="1" fill="#60a5fa" stroke="none" />
                    <circle cx="15" cy="10" r="1" fill="#60a5fa" stroke="none" />
                  </svg>
                  <span class="text-xs tracking-widest text-slate-400">PRODUCT PREVIEW</span>
                </div>
                <div class="absolute top-3 left-3 rounded bg-blue-600 px-2.5 py-1 text-[11px] font-bold text-white">お試し可能</div>
              </div>
              <div class="mt-4">
                <h1 class="mb-2 text-xl font-bold text-balance text-slate-900">{{ product.name }}</h1>
                <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-slate-500">
                  <div class="flex items-center gap-1 font-bold text-slate-900">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="none">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
                    </svg>
                    {{ product.rating }}
                    <span class="font-normal text-slate-400">({{ product.reviewCount }}件)</span>
                  </div>
                  <span>販売実績 {{ product.salesCount.toLocaleString() }}件</span>
                  <span>出品者: <a href="#" class="text-blue-600 hover:text-blue-700">{{ product.seller.name }}</a></span>
                </div>
              </div>
            </div>

            <section class="rounded-lg border border-slate-200 bg-white p-6">
              <h2 class="mb-3.5 text-[15px] font-bold text-slate-900">商品概要</h2>
              <p class="mb-4 text-sm leading-loose text-slate-700">{{ product.description }}</p>
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div v-for="feature in product.features" :key="feature" class="flex items-start gap-2.5 text-[13px] text-slate-700">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" class="mt-0.5 flex-none">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  {{ feature }}
                </div>
              </div>
            </section>

            <section class="rounded-lg border border-slate-200 bg-white p-6">
              <h2 class="mb-4 text-[15px] font-bold text-slate-900">購入者レビュー</h2>
              <div class="flex flex-col gap-4">
                <div
                  v-for="(review, index) in product.reviews"
                  :key="review.author"
                  class="pb-4"
                  :class="{ 'border-b border-slate-100': index < product.reviews.length - 1 }"
                >
                  <div class="mb-1.5 flex justify-between">
                    <span class="text-[13px] font-bold text-slate-900">{{ review.author }}</span>
                    <span class="text-xs text-slate-400">{{ review.date }}</span>
                  </div>
                  <p class="text-[13px] leading-relaxed text-slate-600">{{ review.text }}</p>
                </div>
              </div>
            </section>
          </div>

          <!-- 価格・出品者 -->
          <div class="flex min-w-0 flex-col gap-5">
            <div class="rounded-lg border border-slate-200 bg-white p-6">
              <div class="mb-1.5 flex items-start justify-between gap-3">
                <div class="text-xs text-slate-500">販売価格</div>
                <button type="button" title="お気に入りに追加" class="flex-none p-0.5">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="1.5">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
                  </svg>
                </button>
              </div>
              <div class="mb-4.5 text-[28px] font-bold text-slate-900">¥{{ product.price.toLocaleString() }}</div>
              <NuxtLink
                :to="`/chatbot/${productId}/purchase`"
                class="mb-2.5 block w-full rounded-lg bg-blue-600 py-3 text-center text-[15px] font-bold text-white hover:bg-blue-700"
              >
                今すぐ購入する
              </NuxtLink>
              <button type="button" class="w-full rounded-lg border border-slate-300 bg-white py-3 text-sm font-bold text-slate-700 hover:bg-slate-50">
                カートに入れる
              </button>
              <div class="mt-4.5 flex flex-col gap-2.5 border-t border-slate-100 pt-4.5 text-xs text-slate-600">
                <div class="flex justify-between"><span>提供形式</span><span class="font-bold text-slate-900">{{ product.format }}</span></div>
                <div class="flex justify-between"><span>ライセンス</span><span class="font-bold text-slate-900">{{ product.license }}</span></div>
                <div class="flex justify-between"><span>納品目安</span><span class="font-bold text-slate-900">{{ product.delivery }}</span></div>
              </div>
            </div>

            <section class="rounded-lg border border-slate-200 bg-white p-5">
              <div class="mb-3.5 flex items-center gap-3">
                <div class="flex h-11 w-11 flex-none items-center justify-center rounded-full bg-slate-700 text-[15px] font-bold text-white">
                  {{ product.seller.name.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="text-sm font-bold text-slate-900">{{ product.seller.name }}</div>
                  <div class="text-xs text-slate-500">出品数 {{ product.seller.listingCount }}件 ・ 応答率 {{ product.seller.responseRate }}%</div>
                </div>
              </div>
              <button type="button" class="w-full rounded-lg border border-slate-300 bg-white py-2.5 text-[13px] font-bold text-slate-700 hover:bg-slate-50">
                出品者に質問する
              </button>
            </section>
          </div>
        </div>
      </div>
    </main>

    <CommonAppFooter />
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

const route = useRoute()
const productId = route.params.id

// 商品取得APIが未実装のため、id をキーにしたモックデータで画面を成立させる(バックエンド連携時に置き換え予定)
const mockProducts = {
  '00000000-0000-0000-0000-000000000001': {
    category: 'カスタマーサポート系',
    name: '対応品質評価AI「サポたん」',
    rating: '4.8',
    reviewCount: 212,
    salesCount: 1340,
    description:
      '問い合わせ内容を自動分類し、回答テンプレートを提案するカスタマーサポート特化型チャットボットです。既存のFAQデータを読み込ませるだけで、初回応答率と一次解決率の改善が見込めます。API連携用のPythonサンプルコード、Nuxt向け埋め込みウィジェットも同梱します。',
    features: [
      '日本語・英語のマルチターン対応',
      'Supabase連携の会話ログ保存',
      'Nuxt3向け埋め込みウィジェット付属',
      '納品後30日間の無償サポート',
    ],
    reviews: [
      { author: 'yuki_cs', date: '2026/07/12', text: '導入後、一次回答までの時間が半分になりました。お試しチャットで応答の癖を確認できたので安心して購入できました。' },
      { author: 'm_support', date: '2026/06/29', text: 'Nuxtへの埋め込みが簡単でした。カスタマイズ性ももう少し高いと嬉しいです。' },
    ],
    price: 48000,
    format: 'API + ソースコード一式',
    license: '商用利用可',
    delivery: '購入後 即時',
    seller: { name: 'sapo_lab', listingCount: 18, responseRate: 98 },
    costPerUse: 30,
    startingPoints: 150,
  },
}

const fallbackProduct = {
  category: 'チャットボット',
  name: `チャットボット #${productId}`,
  rating: '-',
  reviewCount: 0,
  salesCount: 0,
  description: 'この商品の詳細情報は準備中です。',
  features: [],
  reviews: [],
  price: 3000,
  format: 'API + ソースコード一式',
  license: '商用利用可',
  delivery: '購入後 即時',
  seller: { name: '出品者未設定', listingCount: 0, responseRate: 0 },
  costPerUse: 30,
  startingPoints: 150,
}

const product = mockProducts[productId] ?? fallbackProduct

useHead({
  title: `${product.name} | botttle`,
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

const BOT_REPLIES = [
  '営業時間は平日9:00〜18:00です。休業日はお問い合わせフォームからご連絡ください。',
  'FAQデータをアップロードいただければ、その内容に沿って自動で回答テンプレートを生成します。',
  '一次解決率の目安は導入企業平均で約72%です。詳細は購入後のレポート機能でご確認いただけます。',
  'ご質問ありがとうございます。他にも気になる点があればお気軽にどうぞ。',
]

const points = ref(product.startingPoints)
const inputText = ref('')
const isSending = ref(false)
const replyIndex = ref(0)
const messages = ref([
  { role: 'bot', text: 'こんにちは！サポたんです。導入前のお試しとして、質問をいくつか送ってみてください。' },
])

const remainingTries = computed(() => Math.floor(points.value / product.costPerUse))
const hasTriesLeft = computed(() => remainingTries.value > 0)
const sendDisabled = computed(() => !hasTriesLeft.value || isSending.value || !inputText.value.trim())

function sendTrialMessage() {
  if (sendDisabled.value) return

  const text = inputText.value.trim()
  messages.value.push({ role: 'user', text })
  points.value -= product.costPerUse
  inputText.value = ''
  isSending.value = true

  setTimeout(() => {
    const reply = BOT_REPLIES[replyIndex.value % BOT_REPLIES.length]
    messages.value.push({ role: 'bot', text: reply })
    replyIndex.value += 1
    isSending.value = false
  }, 900)
}

function rechargePoints() {
  points.value += 300
}
</script>
