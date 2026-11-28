<template>
  <!-- 商品が見つからない(存在しない・非出品・出品者が退会済み・IDの形式が不正) -->
  <CommonPageContainer v-if="notFound">
    <UCard :ui="{ body: 'flex flex-col items-center gap-2 px-6 py-14 text-center sm:px-6 sm:py-14' }">
      <h1 class="text-lg font-bold text-slate-900">商品が見つかりません</h1>
      <p class="mb-4 text-sm text-slate-500">出品が取り下げられたか、URLが間違っている可能性があります。</p>
      <UButton variant="ghost" to="/main">マーケットのトップに戻る</UButton>
    </UCard>
  </CommonPageContainer>

  <!-- 取得失敗(サーバーエラー・通信エラー) -->
  <CommonPageContainer v-else-if="error || !product">
    <UCard :ui="{ body: 'flex flex-col items-center gap-2 px-6 py-14 text-center sm:px-6 sm:py-14' }">
      <h1 class="text-lg font-bold text-slate-900">商品を読み込めませんでした</h1>
      <p class="mb-4 text-sm text-slate-500">時間をおいて再度お試しください。</p>
      <UButton variant="ghost" @click="refresh()">再読み込み</UButton>
    </UCard>
  </CommonPageContainer>

  <!-- 横幅を広く使うため wide にし、広い画面では左右の列を固定幅にして、増えた分を真ん中の列に回す -->
  <CommonPageContainer v-else size="wide">
    <div class="grid grid-cols-1 items-start gap-5 lg:grid-cols-[0.85fr_1.5fr_0.85fr] xl:grid-cols-[300px_minmax(0,1fr)_280px]">
      <!-- 試用チャット -->
      <UCard
        as="section"
        class="flex h-[calc(100vh-7rem)] flex-col lg:sticky lg:top-20"
        :ui="{
          header: 'flex flex-col gap-2.5 px-5 py-4 sm:px-5',
          body: 'flex min-h-0 flex-1 flex-col p-0 sm:p-0',
          footer: 'px-5 py-3.5 sm:px-5',
        }"
      >
        <template #header>
          <div>
            <CommonSectionTitle class="mb-1">お試しチャット</CommonSectionTitle>
            <p class="text-xs text-slate-500">1回の送信につき {{ TRIAL_COST_PER_USE }}pt を消費します</p>
          </div>
          <div class="flex items-center justify-between bg-primary-50 px-3 py-2 text-sm">
            <span class="text-slate-700">残り試用回数</span>
            <span class="font-bold whitespace-nowrap text-slate-900">{{ remainingTries }}回</span>
          </div>
        </template>

        <CommonChatLog class="bg-slate-50 px-5 py-4" aria-label="お試しチャットの会話">
          <CommonChatBubble v-for="(msg, index) in messages" :key="index" :sender="msg.role" :avatar="botInitial">
            {{ msg.text }}
          </CommonChatBubble>
          <CommonTypingIndicator v-if="isSending" :avatar="botInitial" />
        </CommonChatLog>

        <template #footer>
          <!-- form にして Enter で送信する(日本語の変換確定の Enter では送信されない) -->
          <form v-if="hasTriesLeft" class="flex flex-col gap-2" @submit.prevent="sendTrialMessage">
            <UInput v-model="inputText" class="w-full" placeholder="質問を入力（例：営業時間を教えて）" aria-label="質問" />
            <UButton type="submit" block :disabled="sendDisabled">送信（{{ TRIAL_COST_PER_USE }}pt）</UButton>
          </form>
          <div v-else class="flex items-center justify-between gap-3 border border-red-200 bg-red-50 px-4 py-3.5">
            <span class="text-sm text-red-800">BC残高が不足しています。BCをチャージするとお試しを続けられます。</span>
            <UButton size="sm" class="flex-none" @click="rechargePoints">BCをチャージ</UButton>
          </div>
        </template>
      </UCard>

      <!-- サムネイル・商品概要・レビュー -->
      <div class="flex min-w-0 flex-col gap-6">
        <div>
          <div class="relative flex aspect-video items-center justify-center overflow-hidden bg-slate-900">
            <ProductThumbnail :src="product.thumbnail_url" :alt="product.bot_name" loading="eager">
              <div class="flex flex-col items-center gap-3 text-primary-400">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  <circle cx="9" cy="10" r="1" fill="currentColor" stroke="none" />
                  <circle cx="15" cy="10" r="1" fill="currentColor" stroke="none" />
                </svg>
                <span class="text-xs tracking-widest text-slate-400">PRODUCT PREVIEW</span>
              </div>
            </ProductThumbnail>
            <UBadge class="absolute top-3 left-3 font-bold">お試し可能</UBadge>
          </div>
          <div class="mt-4">
            <span v-if="product.category_name" class="mb-2" :class="categoryTagClass(product.category_id)">{{ product.category_name }}</span>
            <h1 class="mb-2 text-2xl font-bold text-balance text-slate-900">{{ product.bot_name }}</h1>
            <div class="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-slate-500">
              <div class="flex items-center gap-1 font-bold text-slate-900">
                <svg class="fill-amber-500" width="14" height="14" viewBox="0 0 24 24" stroke="none" aria-hidden="true">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
                </svg>
                {{ displayRating }}
                <span class="font-normal text-slate-500">({{ displayReviewCount }}件)</span>
              </div>
              <span>出品者: <a href="#" class="text-primary hover:underline">{{ sellerName }}</a></span>
            </div>
          </div>
        </div>

        <UCard as="section">
          <CommonSectionTitle class="mb-3">商品概要</CommonSectionTitle>
          <p v-if="product.description" class="text-sm leading-loose whitespace-pre-line text-slate-700">{{ product.description }}</p>
          <p v-else class="text-sm text-slate-500">説明はまだありません。</p>
        </UCard>

        <ReviewsBotReviewSection
          :chatbot-id="productId"
          mock-enabled
          @summary="updateReviewSummary"
        />
      </div>

      <!-- 価格・出品者 -->
      <div class="flex min-w-0 flex-col gap-5">
        <UCard>
          <div class="mb-1.5 flex items-start justify-between gap-3">
            <div class="text-xs text-slate-500">販売価格</div>
            <UButton
              color="neutral"
              variant="ghost"
              size="sm"
              square
              aria-label="お気に入りに追加"
              title="お気に入りに追加"
              class="-mt-1.5 -mr-2"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
              </svg>
            </UButton>
          </div>
          <div class="mb-4 text-3xl font-bold text-slate-900">{{ formatPrice(product.price) }}</div>
          <div class="flex flex-col gap-2.5">
            <UButton block size="lg" :disabled="!canPurchase" @click="buyNow">今すぐ購入する</UButton>
            <UButton v-if="inCart && isLoggedIn" block size="lg" variant="outline" to="/cart">カートに追加済み（カートを見る）</UButton>
            <UButton v-else block size="lg" variant="outline" :disabled="!canPurchase" @click="addToCart">カートに入れる</UButton>
          </div>
          <p v-if="!isLoggedIn" class="mt-2.5 text-center text-xs text-slate-500">
            購入するには<NuxtLink to="/login" class="font-bold text-primary hover:underline">ログイン</NuxtLink>が必要です
          </p>
          <p v-else-if="product.price === null" class="mt-2.5 text-center text-xs text-slate-500">
            価格が設定されていないため、購入できません
          </p>
        </UCard>

        <UCard as="section">
          <div class="mb-4 flex items-center gap-3">
            <div class="flex size-11 flex-none items-center justify-center rounded-full bg-primary-100 text-base font-bold text-primary-700" aria-hidden="true">
              {{ sellerName.charAt(0).toUpperCase() }}
            </div>
            <div class="text-sm font-bold text-slate-900">{{ sellerName }}</div>
          </div>
          <UButton block variant="outline">出品者に質問する</UButton>
        </UCard>
      </div>
    </div>
  </CommonPageContainer>
</template>

<script setup>
const route = useRoute()
const productId = computed(() => String(route.params.id))

const { data: product, error, refresh } = await useProduct(productId)

// 400(IDの形式が不正)も、利用者から見れば「その商品は無い」なので同じ表示にする
const notFound = computed(() => [400, 404].includes(error.value?.statusCode))

const sellerName = computed(() => product.value?.username || '出品者不明')
// お試しチャットで、ボットの吹き出しの横に出すアイコンの文字
const botInitial = computed(() => product.value?.bot_name?.charAt(0) || 'B')

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
