<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <main class="flex-1">
      <!-- 商品が見つからない(存在しない・非出品・出品者が退会済み・IDの形式が不正) -->
      <div v-if="notFound" class="mx-auto max-w-6xl px-6 py-16">
        <div class="rounded-lg border border-slate-200 bg-white px-6 py-14 text-center">
          <h1 class="mb-2 text-lg font-bold text-slate-900">商品が見つかりません</h1>
          <p class="mb-6 text-sm text-slate-500">出品が取り下げられたか、URLが間違っている可能性があります。</p>
          <NuxtLink to="/main" class="text-sm font-bold text-blue-600 hover:text-blue-700">マーケットのトップに戻る</NuxtLink>
        </div>
      </div>

      <!-- 取得失敗(サーバーエラー・通信エラー) -->
      <div v-else-if="error || !product" class="mx-auto max-w-6xl px-6 py-16">
        <div class="rounded-lg border border-slate-200 bg-white px-6 py-14 text-center">
          <h1 class="mb-2 text-lg font-bold text-slate-900">商品を読み込めませんでした</h1>
          <p class="mb-6 text-sm text-slate-500">時間をおいて再度お試しください。</p>
          <button type="button" class="text-sm font-bold text-blue-600 hover:text-blue-700" @click="refresh()">再読み込み</button>
        </div>
      </div>

      <div v-else class="mx-auto max-w-6xl px-6 py-6">
        <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[0.85fr_1.5fr_0.85fr]">
          <!-- 試用チャット -->
          <section class="flex h-[calc(100vh-7rem)] flex-col overflow-hidden rounded-lg border border-slate-200 bg-white lg:sticky lg:top-20">
            <div class="flex flex-col gap-2.5 border-b border-slate-200 px-5 py-4">
              <div>
                <h2 class="mb-1 text-[15px] font-bold text-slate-900">お試しチャット</h2>
                <p class="text-xs text-slate-500">1回の送信につき {{ TRIAL_COST_PER_USE }}pt を消費します</p>
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
                  送信（{{ TRIAL_COST_PER_USE }}pt）
                </button>
              </div>
              <div v-else class="flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3.5">
                <span class="text-[13px] text-red-800">BC残高が不足しています。BCをチャージするとお試しを続けられます。</span>
                <button
                  type="button"
                  class="flex-none rounded-md bg-slate-700 px-4 py-2 text-[12.5px] font-bold whitespace-nowrap text-white hover:bg-slate-800"
                  @click="rechargePoints"
                >
                  BCをチャージ
                </button>
              </div>
            </div>
          </section>

          <!-- サムネイル・商品概要・レビュー -->
          <div class="flex min-w-0 flex-col gap-6">
            <div>
              <div class="relative flex aspect-video items-center justify-center overflow-hidden rounded-xl bg-slate-900">
                <ProductThumbnail :src="product.thumbnail_url" :alt="product.bot_name" loading="eager">
                  <div class="flex flex-col items-center gap-3 text-slate-300">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="1.5">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      <circle cx="9" cy="10" r="1" fill="#60a5fa" stroke="none" />
                      <circle cx="15" cy="10" r="1" fill="#60a5fa" stroke="none" />
                    </svg>
                    <span class="text-xs tracking-widest text-slate-400">PRODUCT PREVIEW</span>
                  </div>
                </ProductThumbnail>
                <div class="absolute top-3 left-3 rounded bg-blue-600 px-2.5 py-1 text-[11px] font-bold text-white">お試し可能</div>
              </div>
              <div class="mt-4">
                <span v-if="product.category_name" class="mb-2" :class="categoryTagClass(product.category_id)">{{ product.category_name }}</span>
                <h1 class="mb-2 text-xl font-bold text-balance text-slate-900">{{ product.bot_name }}</h1>
                <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-slate-500">
                  <div class="flex items-center gap-1 font-bold text-slate-900">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="none">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
                    </svg>
                    {{ displayRating }}
                    <span class="font-normal text-slate-400">({{ displayReviewCount }}件)</span>
                  </div>
                  <span>出品者: <a href="#" class="text-blue-600 hover:text-blue-700">{{ sellerName }}</a></span>
                </div>
              </div>
            </div>

            <section class="rounded-lg border border-slate-200 bg-white p-6">
              <h2 class="mb-3.5 text-[15px] font-bold text-slate-900">商品概要</h2>
              <p v-if="product.description" class="text-sm leading-loose whitespace-pre-line text-slate-700">{{ product.description }}</p>
              <p v-else class="text-sm text-slate-400">説明はまだありません。</p>
            </section>

            <ReviewsBotReviewSection
              :chatbot-id="productId"
              mock-enabled
              @summary="updateReviewSummary"
            />
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
              <div class="mb-4.5 text-[28px] font-bold text-slate-900">{{ formatPrice(product.price) }}</div>
              <button
                type="button"
                class="mb-2.5 block w-full rounded-lg bg-blue-600 py-3 text-center text-[15px] font-bold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:hover:bg-slate-300"
                :disabled="!canPurchase"
                @click="buyNow"
              >
                今すぐ購入する
              </button>
              <NuxtLink
                v-if="inCart && isLoggedIn"
                to="/cart"
                class="block w-full rounded-lg border border-blue-600 bg-white py-3 text-center text-sm font-bold text-blue-600 hover:bg-blue-50"
              >
                カートに追加済み（カートを見る）
              </NuxtLink>
              <button
                v-else
                type="button"
                class="w-full rounded-lg border border-slate-300 bg-white py-3 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400 disabled:hover:bg-slate-100"
                :disabled="!canPurchase"
                @click="addToCart"
              >
                カートに入れる
              </button>
              <p v-if="!isLoggedIn" class="mt-2.5 text-center text-xs text-slate-500">
                購入するには<NuxtLink to="/login" class="font-bold text-blue-600 hover:text-blue-700">ログイン</NuxtLink>が必要です
              </p>
              <p v-else-if="product.price === null" class="mt-2.5 text-center text-xs text-slate-500">
                価格が設定されていないため、購入できません
              </p>
            </div>

            <section class="rounded-lg border border-slate-200 bg-white p-5">
              <div class="mb-3.5 flex items-center gap-3">
                <div class="flex h-11 w-11 flex-none items-center justify-center rounded-full bg-slate-700 text-[15px] font-bold text-white">
                  {{ sellerName.charAt(0).toUpperCase() }}
                </div>
                <div class="text-sm font-bold text-slate-900">{{ sellerName }}</div>
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
const productId = computed(() => String(route.params.id))

const { data: product, error, refresh } = await useProduct(productId)

// 400(IDの形式が不正)も、利用者から見れば「その商品は無い」なので同じ表示にする
const notFound = computed(() => [400, 404].includes(error.value?.statusCode))

const sellerName = computed(() => product.value?.username || '出品者不明')

// 評価はレビュー欄(ReviewsBotReviewSection)が読み込んだ値で更新する。読み込むまでは「-」と0件
const liveAverageRating = ref(null)
const liveReviewCount = ref(null)
const displayRating = computed(() => (liveAverageRating.value === null ? '-' : liveAverageRating.value.toFixed(1)))
const displayReviewCount = computed(() => liveReviewCount.value ?? 0)

function updateReviewSummary({ averageRating, reviewCount }) {
  liveAverageRating.value = averageRating
  liveReviewCount.value = reviewCount
}

useHead({
  title: () => {
    if (product.value) return `${product.value.bot_name} | botttle`
    return notFound.value ? '商品が見つかりません | botttle' : 'botttle'
  },
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

// お試しチャットはまだバックエンドが無いため、返答・ポイントともにモック(バックエンド連携時に置き換え予定)
const TRIAL_COST_PER_USE = 30
const TRIAL_STARTING_POINTS = 150

const BOT_REPLIES = [
  '営業時間は平日9:00〜18:00です。休業日はお問い合わせフォームからご連絡ください。',
  'FAQデータをアップロードいただければ、その内容に沿って自動で回答テンプレートを生成します。',
  '一次解決率の目安は導入企業平均で約72%です。詳細は購入後のレポート機能でご確認いただけます。',
  'ご質問ありがとうございます。他にも気になる点があればお気軽にどうぞ。',
]

const points = ref(TRIAL_STARTING_POINTS)
const inputText = ref('')
const isSending = ref(false)
const replyIndex = ref(0)
const messages = ref([
  {
    role: 'bot',
    text: `こんにちは！${product.value?.bot_name ?? 'チャットボット'}です。導入前のお試しとして、質問をいくつか送ってみてください。`,
  },
])

const remainingTries = computed(() => Math.floor(points.value / TRIAL_COST_PER_USE))
const hasTriesLeft = computed(() => remainingTries.value > 0)
const sendDisabled = computed(() => !hasTriesLeft.value || isSending.value || !inputText.value.trim())

function sendTrialMessage() {
  if (sendDisabled.value) return

  const text = inputText.value.trim()
  messages.value.push({ role: 'user', text })
  points.value -= TRIAL_COST_PER_USE
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

// 購入は単品でも必ずカートを経由する
// 未ログイン時・価格未設定の商品は購入・カート追加ボタンを無効化する(カート画面自体もauthミドルウェアで保護)
const { isLoggedIn } = storeToRefs(useAuthStore())
const cartStore = useCartStore()
// URLのIDは大文字やハイフン無しでも通るため、カートにはAPIが返した正規化済みのIDで入れ、判定もそれで行う
const inCart = computed(() => Boolean(product.value) && cartStore.has(product.value.chatbot_id))
const canPurchase = computed(() => isLoggedIn.value && product.value?.price != null)

function addToCart() {
  if (!canPurchase.value) return
  const item = product.value
  cartStore.add({
    id: item.chatbot_id,
    name: item.bot_name,
    seller: sellerName.value,
    price: item.price,
    tags: item.category_name ? [item.category_name] : [],
  })
}

function buyNow() {
  if (!canPurchase.value) return
  addToCart()
  navigateTo('/cart')
}
</script>
