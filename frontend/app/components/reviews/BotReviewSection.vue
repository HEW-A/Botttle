<template>
  <section class="rounded-lg border border-slate-200 bg-white p-6">
    <div class="mb-5 flex flex-wrap items-center justify-between gap-2">
      <h2 class="text-[15px] font-bold text-slate-900">購入者レビュー</h2>
      <div class="text-sm text-slate-600">
        平均 <span class="font-bold text-slate-900">{{ averageDisplay }}</span>
        <span class="text-xs text-slate-400">（{{ reviewCount }}件）</span>
      </div>
    </div>

    <div v-if="canUseReviewForm && myReviewLoading" class="mb-5 text-sm text-slate-500">
      購入情報を確認しています…
    </div>

    <form
      v-else-if="canUseReviewForm && canReview && (!hasExistingReview || isEditing)"
      class="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4"
      @submit.prevent="submitReview"
    >
      <h3 class="mb-3 text-sm font-bold text-slate-900">
        {{ hasExistingReview ? 'レビューを更新する' : 'このボットを評価する' }}
      </h3>
      <p class="mb-3 text-xs text-slate-600">
        {{ hasExistingReview
          ? '投稿済みの評価とコメントを書き換えられます。'
          : 'レビューは1人につき1件まで投稿できます。' }}
      </p>

      <div class="mb-3">
        <span class="mb-1.5 block text-xs font-bold text-slate-700">評価</span>
        <span
          class="flex w-fit gap-1"
          role="radiogroup"
          aria-label="評価"
          @mouseleave="hoveredRating = 0"
        >
          <button
            v-for="star in 5"
            :key="star"
            type="button"
            role="radio"
            :aria-label="`${star}点`"
            :aria-checked="ratingInput === star"
            class="rounded p-0.5 transition-colors focus:outline-none"
            @mouseenter="hoveredRating = star"
            @focus="hoveredRating = star"
            @blur="hoveredRating = 0"
            @click="ratingInput = star"
          >
            <svg
              class="h-8 w-8"
              viewBox="0 0 24 24"
              :fill="star <= (hoveredRating || Number(ratingInput)) ? '#f59e0b' : '#e2e8f0'"
              aria-hidden="true"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
            </svg>
          </button>
        </span>
      </div>

      <label class="block">
        <span class="mb-1.5 block text-xs font-bold text-slate-700">
          コメント<span class="ml-1 font-normal text-slate-400">（任意）</span>
        </span>
        <textarea
          v-model="commentInput"
          maxlength="1000"
          rows="4"
          placeholder="このボットを使った感想を入力してください"
          class="w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-2 text-sm leading-relaxed text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
        ></textarea>
        <span class="mt-1 block text-right text-[11px] text-slate-400">{{ commentInput.length }}/1000</span>
      </label>

      <p v-if="saveError" class="mb-3 text-xs text-red-600">{{ saveError }}</p>

      <div class="flex flex-wrap gap-2">
        <button
          type="submit"
          :disabled="!canSubmit || saving"
          class="rounded-md bg-blue-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {{ saving ? '保存中…' : hasExistingReview ? 'レビューを更新' : 'レビューを投稿' }}
        </button>
        <button
          v-if="hasExistingReview"
          type="button"
          :disabled="saving"
          class="rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-bold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:text-slate-400"
          @click="cancelEditing"
        >
          キャンセル
        </button>
      </div>
    </form>

    <!-- 自分のレビューは GET /review の結果で出す(一覧のページに含まれていなくても表示できる) -->
    <div
      v-else-if="canUseReviewForm && canReview && myReview"
      class="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4"
    >
      <div class="mb-1.5 flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
          <h3 class="text-sm font-bold text-slate-900">あなたのレビュー</h3>
          <span
            class="flex gap-0.5"
            role="img"
            :aria-label="`評価${myReview.rating}点（5点満点）`"
          >
            <svg
              v-for="star in 5"
              :key="star"
              class="h-4 w-4"
              viewBox="0 0 24 24"
              :fill="star <= myReview.rating ? '#f59e0b' : '#e2e8f0'"
              aria-hidden="true"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
            </svg>
          </span>
        </div>
        <div class="flex items-center gap-3">
          <time class="text-xs text-slate-400">{{ formatDate(myReview.reviewed_at) }}</time>
          <button
            type="button"
            class="rounded border border-blue-200 bg-white px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-50"
            @click="startEditing"
          >
            レビュー変更
          </button>
        </div>
      </div>
      <p v-if="myReview.comment" class="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-600">{{ myReview.comment }}</p>
      <p v-if="saveMessage" class="mt-2 text-xs font-bold text-green-700">{{ saveMessage }}</p>
    </div>

    <p v-else-if="canUseReviewForm && myReviewError" class="mb-5 text-xs text-red-600">{{ myReviewError }}</p>
    <p v-else-if="canUseReviewForm && !canReview && !myReviewLoading" class="mb-5 rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-500">
      このボットを購入したユーザーのみレビューを投稿できます。
    </p>
    <p v-else-if="!canUseReviewForm" class="mb-5 rounded-md bg-slate-50 px-4 py-3 text-xs text-slate-500">
      購入済みの方は、ログインするとレビューを投稿できます。
    </p>

    <p v-if="loadError" class="mb-4 text-xs text-red-600">{{ loadError }}</p>
    <p v-if="reviewsLoading" class="text-sm text-slate-500">レビューを読み込んでいます…</p>
    <p v-else-if="reviews.length === 0" class="text-sm text-slate-500">まだレビューはありません。</p>

    <div v-else class="flex flex-col gap-4">
      <article
        v-for="(review, index) in reviews"
        :key="review.username ?? index"
        class="pb-4"
        :class="{ 'border-b border-slate-100': index < reviews.length - 1 }"
      >
        <div class="mb-1.5 flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span class="text-[13px] font-bold text-slate-900">{{ review.username || '購入者' }}</span>
            <span
              class="flex gap-0.5"
              role="img"
              :aria-label="`評価${review.rating}点（5点満点）`"
            >
              <svg
                v-for="star in 5"
                :key="star"
                class="h-4 w-4"
                viewBox="0 0 24 24"
                :fill="star <= review.rating ? '#f59e0b' : '#e2e8f0'"
                aria-hidden="true"
              >
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z" />
              </svg>
            </span>
          </div>
          <time class="text-xs text-slate-400">{{ formatDate(review.reviewed_at) }}</time>
        </div>
        <p v-if="review.comment" class="whitespace-pre-wrap text-[13px] leading-relaxed text-slate-600">{{ review.comment }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
// API: GET  /api/products/<id>/reviews  一覧と平均・件数(ログイン不要)
//      GET  /api/products/<id>/review   自分のレビューと購入済みかどうか
//      PUT  /api/products/<id>/review   投稿・上書き
interface Review {
  username: string | null
  rating: number
  comment: string | null
  reviewed_at: string | null
}

interface ReviewListResponse {
  rating_avg: number | null
  review_count: number
  reviews: Review[]
}

interface MyReview {
  rating: number
  comment: string | null
  reviewed_at: string | null
}

interface MyReviewResponse {
  purchased: boolean
  review: MyReview | null
}

// 一覧APIの上限。ページ送りは未実装のため、最大件数で取得する
const REVIEW_LIMIT = 100
const MOCK_USERNAME = 'モック購入者'

const props = withDefaults(
  defineProps<{
    chatbotId: string
    mockEnabled?: boolean
  }>(),
  {
    mockEnabled: false,
  },
)
const emit = defineEmits<{
  summary: [value: { averageRating: number | null; reviewCount: number }]
}>()

const config = useRuntimeConfig()
const { isLoggedIn } = storeToRefs(useAuthStore())

// 商品画面から明示されたローカル開発時だけ有効。本番ビルドでは常にfalseになる。
const mockMode = computed(() => import.meta.dev && props.mockEnabled)
const canUseReviewForm = computed(() => isLoggedIn.value || mockMode.value)

const reviews = ref<Review[]>([])
const averageRating = ref<number | null>(null)
const reviewCount = ref(0)
const reviewsLoading = ref(true)
const myReviewLoading = ref(false)
const loadError = ref('')
const myReviewError = ref('')

const canReview = ref(false)
const myReview = ref<MyReview | null>(null)
const hasExistingReview = computed(() => myReview.value !== null)
const isEditing = ref(false)
const ratingInput = ref<number | ''>('')
const hoveredRating = ref(0)
const commentInput = ref('')
const saving = ref(false)
const saveError = ref('')
const saveMessage = ref('')

const averageDisplay = computed(() =>
  averageRating.value === null ? '-' : averageRating.value.toFixed(1),
)
const canSubmit = computed(() => {
  const rating = Number(ratingInput.value)
  return (
    ratingInput.value !== '' &&
    Number.isInteger(rating) &&
    rating >= 1 &&
    rating <= 5 &&
    commentInput.value.length <= 1000
  )
})

function apiErrorMessage(error: unknown, fallback: string) {
  const fetchError = error as { data?: { error?: string } }
  return fetchError?.data?.error || fallback
}

function emitSummary() {
  emit('summary', {
    averageRating: averageRating.value,
    reviewCount: reviewCount.value,
  })
}

function resetInputs() {
  ratingInput.value = myReview.value?.rating ?? ''
  commentInput.value = myReview.value?.comment ?? ''
  hoveredRating.value = 0
}

async function loadReviews() {
  reviewsLoading.value = true
  loadError.value = ''
  if (mockMode.value) {
    updateMockSummary()
    reviewsLoading.value = false
    return
  }

  try {
    const result = await $fetch<ReviewListResponse>(
      `/api/products/${props.chatbotId}/reviews`,
      {
        baseURL: config.public.apiBase,
        query: { limit: REVIEW_LIMIT },
      },
    )
    reviews.value = result.reviews
    averageRating.value = result.rating_avg
    reviewCount.value = result.review_count
    emitSummary()
  } catch (error) {
    loadError.value = apiErrorMessage(error, 'レビューの読み込みに失敗しました。')
  } finally {
    reviewsLoading.value = false
  }
}

async function loadMyReview() {
  canReview.value = false
  myReview.value = null
  isEditing.value = false
  myReviewError.value = ''
  saveError.value = ''
  saveMessage.value = ''
  resetInputs()

  if (mockMode.value) {
    canReview.value = true
    return
  }

  if (!isLoggedIn.value) return

  myReviewLoading.value = true
  try {
    const result = await $fetch<MyReviewResponse>(
      `/api/products/${props.chatbotId}/review`,
      {
        baseURL: config.public.apiBase,
        credentials: 'include',
      },
    )
    canReview.value = result.purchased
    myReview.value = result.review
    resetInputs()
  } catch (error) {
    // フォームが出ない状態でも見えるよう、投稿エラーとは別に表示する
    myReviewError.value = apiErrorMessage(error, '購入情報の確認に失敗しました。')
  } finally {
    myReviewLoading.value = false
  }
}

async function submitReview() {
  if (!canSubmit.value || saving.value) return

  saving.value = true
  saveError.value = ''
  saveMessage.value = ''
  const rating = Number(ratingInput.value)
  // 空白だけのコメントは本文なしとして送る(APIも同じ扱い)
  const comment = commentInput.value.trim() || null
  try {
    if (mockMode.value) {
      const now = new Date().toISOString()
      const mockReview: Review = {
        username: MOCK_USERNAME,
        rating,
        comment,
        reviewed_at: now,
      }
      const existingIndex = reviews.value.findIndex(review => review.username === MOCK_USERNAME)
      if (existingIndex === -1) {
        reviews.value.unshift(mockReview)
      } else {
        reviews.value.splice(existingIndex, 1)
        reviews.value.unshift(mockReview)
      }
      myReview.value = { rating, comment, reviewed_at: now }
      isEditing.value = false
      saveMessage.value = 'モックレビューを画面に反映しました。'
      updateMockSummary()
      return
    }

    myReview.value = await $fetch<MyReview>(`/api/products/${props.chatbotId}/review`, {
      baseURL: config.public.apiBase,
      method: 'PUT',
      credentials: 'include',
      body: { rating, comment },
    })
    isEditing.value = false
    saveMessage.value = 'レビューを保存しました。'
    await loadReviews()
  } catch (error) {
    saveError.value = apiErrorMessage(error, 'レビューの保存に失敗しました。')
  } finally {
    saving.value = false
  }
}

function startEditing() {
  if (!hasExistingReview.value) return
  resetInputs()
  saveError.value = ''
  saveMessage.value = ''
  isEditing.value = true
}

function cancelEditing() {
  resetInputs()
  saveError.value = ''
  saveMessage.value = ''
  isEditing.value = false
}

function updateMockSummary() {
  reviewCount.value = reviews.value.length
  averageRating.value = reviewCount.value
    ? reviews.value.reduce((total, review) => total + review.rating, 0) /
      reviewCount.value
    : null
  emitSummary()
}

function formatDate(value: string | null) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleDateString('ja-JP')
}

onMounted(async () => {
  await Promise.all([loadReviews(), loadMyReview()])
})

watch(isLoggedIn, () => {
  if (import.meta.client) loadMyReview()
})
</script>
