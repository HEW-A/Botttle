<template>
  <CommonPageContainer size="narrow">
    <UCard v-if="loading" :ui="{ body: 'px-8 py-16 text-center sm:px-8 sm:py-16' }">
      <p class="text-sm text-slate-500" role="status">出品情報を読み込んでいます…</p>
    </UCard>

    <UCard v-else-if="loadError" :ui="{ body: 'flex flex-col items-center gap-4 px-8 py-16 text-center sm:px-8 sm:py-16' }">
      <p class="text-sm font-bold text-red-600" role="alert">{{ loadError }}</p>
      <UButton variant="outline" to="/chatbot/creation">Bot作成画面へ戻る</UButton>
    </UCard>

    <UCard v-else-if="published" :ui="{ body: 'flex flex-col items-center gap-5 px-8 py-16 text-center sm:px-8 sm:py-16' }">
      <div class="flex size-14 items-center justify-center rounded-full border-2 border-primary text-primary">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20 6L9 17l-5-5"></path>
        </svg>
      </div>
      <div class="flex flex-col gap-2">
        <h1 class="text-2xl font-bold text-slate-900">{{ completionMode === 'update' ? '出品内容を更新しました' : '出品が完了しました' }}</h1>
        <p class="text-sm text-slate-500">「{{ name }}」を{{ completionMode === 'update' ? '更新しました。' : 'マーケットに公開しました。' }}</p>
      </div>
      <div class="flex flex-wrap justify-center gap-3">
        <UButton :to="`/chatbot/${chatbotId}`">出品したボットを確認</UButton>
        <UButton variant="outline" @click="createAnotherBot">続けて出品する</UButton>
      </div>
    </UCard>

    <template v-else>
      <CommonPageHeader
        :title="isListed ? 'チャットボットの出品内容を更新する' : 'チャットボットを出品する'"
        :description="isListed ? '現在の出品内容を変更できます。' : '必要事項を入力して、マーケットに公開しましょう。'"
      />

      <UCard :ui="{ body: 'flex flex-col gap-6 p-8 sm:p-8' }">
        <div class="flex items-start gap-4">
          <input
            ref="fileInputRef"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            class="hidden"
            @change="handleFileChange"
          />
          <!-- クリックでもキーボード(Enter/Space)でも画像を選べるよう button にしている -->
          <button
            type="button"
            :aria-label="thumbnail ? 'サムネイル画像を変更' : 'サムネイル画像を追加'"
            class="flex size-28 flex-none cursor-pointer flex-col items-center justify-center overflow-hidden border-2 border-dashed transition-colors focus-visible:outline-2 focus-visible:outline-primary"
            :class="dragOver ? 'border-primary bg-primary-50' : 'border-slate-300 bg-slate-50 hover:border-primary'"
            @click="openPicker"
            @drop.prevent="handleDrop"
            @dragover.prevent="dragOver = true"
            @dragleave="dragOver = false"
          >
            <img v-if="thumbnail" :src="thumbnail" alt="" class="size-full object-cover" />
            <template v-else>
              <svg class="text-slate-400" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="3" y="6" width="18" height="14" rx="0"></rect>
                <circle cx="12" cy="13" r="3.5"></circle>
                <path d="M8 6l1.2-2h5.6L16 6"></path>
              </svg>
              <span class="mt-1.5 text-xs text-slate-500">画像を追加</span>
            </template>
          </button>
          <p class="pt-1.5 text-xs leading-relaxed text-slate-500">
            ボットのロゴやチャット画面のスクリーンショットがあると購入されやすくなります。
            <span class="mt-1 block">JPEG・PNG・WebP、5MB以内</span>
          </p>
        </div>

        <div class="flex flex-col gap-1.5">
          <label for="listing-name" class="text-xs font-bold text-slate-700">商品名</label>
          <UInput id="listing-name" v-model="name" class="w-full" :maxlength="40" placeholder="例: 領収書仕分けボット" />
        </div>

        <div class="flex flex-col gap-1.5">
          <label for="listing-category" class="text-xs font-bold text-slate-700">カテゴリ</label>
          <!-- USelect は矢印のアイコンを外部(Iconify)から取得するため、ブラウザ標準の select を UInput と同じ見た目にしている -->
          <select
            id="listing-category"
            v-model="category"
            class="h-11 w-full rounded-control bg-white px-3.5 text-sm text-slate-900 ring ring-slate-300 ring-inset focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
          >
            <option value="">選択してください</option>
            <option v-for="c in categories" :key="c.category_id" :value="String(c.category_id)">{{ c.category_name }}</option>
          </select>
        </div>

        <div class="flex flex-col gap-1.5">
          <label for="listing-price" class="text-xs font-bold text-slate-700">販売価格</label>
          <UInput
            id="listing-price"
            :model-value="price"
            class="w-full"
            type="text"
            inputmode="numeric"
            placeholder="0"
            @input="handlePriceInput"
          >
            <template #trailing>
              <span class="text-sm text-slate-500">{{ CURRENCY_UNIT }}</span>
            </template>
          </UInput>
        </div>

        <div class="flex flex-col gap-1.5">
          <label for="listing-description" class="text-xs font-bold text-slate-700">説明文</label>
          <UTextarea
            id="listing-description"
            v-model="description"
            class="w-full"
            :ui="{ base: 'resize-y leading-relaxed' }"
            :rows="5"
            :maxlength="5000"
            placeholder="どんなことができるボットか、使い方や注意点を書いてください"
          />
        </div>

        <p v-if="formError" class="text-sm font-bold text-red-600" role="alert">{{ formError }}</p>

        <UButton block size="lg" :disabled="!canSubmit || submitting" @click="openPreview">
          {{ submitting ? (isListed ? '更新中…' : '出品中…') : (isListed ? '出品内容を更新する' : '出品する') }}
        </UButton>
      </UCard>
    </template>

    <!-- 出品前の確認 -->
    <UModal
      v-model:open="previewOpen"
      :title="isListed ? 'この内容で更新しますか？' : 'この内容で出品しますか？'"
      :dismissible="!submitting"
      :ui="{ content: 'sm:max-w-md' }"
    >
      <template #content>
        <div class="flex h-40 w-full items-center justify-center overflow-hidden bg-slate-200">
          <img v-if="thumbnail" :src="thumbnail" alt="サムネイルのプレビュー" class="size-full object-cover" />
          <svg v-else class="text-slate-400" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="6" width="18" height="14" rx="0"></rect>
            <circle cx="12" cy="13" r="3.5"></circle>
          </svg>
        </div>
        <div class="flex flex-col gap-2.5 p-6">
          <span :class="categoryTagClass(Number(category))">{{ categoryDisplay }}</span>
          <p class="text-lg font-bold text-slate-900">{{ name }}</p>
          <p class="max-h-20 overflow-auto text-sm leading-relaxed whitespace-pre-line text-slate-500">{{ description }}</p>
          <p class="text-xl font-bold text-slate-900">{{ formatPrice(Number(price) || 0) }}</p>
          <div class="mt-2.5 flex gap-2.5">
            <UButton variant="outline" class="flex-1 justify-center" :disabled="submitting" @click="closePreview">編集に戻る</UButton>
            <UButton class="flex-1 justify-center" :disabled="submitting" @click="confirmPublish">
              {{ submitting ? (isListed ? '更新中…' : '出品中…') : (isListed ? 'この内容で更新する' : 'この内容で出品する') }}
            </UButton>
          </div>
          <p v-if="formError" class="text-sm font-bold text-red-600" role="alert">{{ formError }}</p>
        </div>
      </template>
    </UModal>
  </CommonPageContainer>
</template>

<script setup>
definePageMeta({
  middleware: 'auth',
})

useHead({
  title: 'チャットボットを出品する | botttle',
})

const route = useRoute()
const config = useRuntimeConfig()
const chatbotId = computed(() => String(route.params.id))

const categories = ref([])

const fileInputRef = ref(null)
const dragOver = ref(false)
const thumbnail = ref(null)
const thumbnailFile = ref(null)
const name = ref('')
const category = ref('')
const price = ref('')
const description = ref('')
const previewOpen = ref(false)
const published = ref(false)
const isListed = ref(false)
const completionMode = ref('publish')
const loading = ref(true)
const submitting = ref(false)
const loadError = ref('')
const formError = ref('')

const canSubmit = computed(() => {
  const numericPrice = Number(price.value)
  return !!(
    name.value.trim() &&
    category.value &&
    description.value.trim() &&
    price.value &&
    Number.isSafeInteger(numericPrice) &&
    numericPrice >= 1 &&
    numericPrice <= 2147483647
  )
})
const categoryDisplay = computed(() => (
  categories.value.find((item) => String(item.category_id) === category.value)?.category_name || ''
))

function apiErrorMessage(error, fallback) {
  const message = error?.data?.error || fallback
  if (import.meta.dev && error?.data?.detail) {
    return `${message}（${error.data.detail}）`
  }
  return message
}

async function loadListing() {
  loading.value = true
  loadError.value = ''
  try {
    const result = await $fetch(`/api/listings/${chatbotId.value}`, {
      baseURL: config.public.apiBase,
      credentials: 'include',
    })
    const bot = result.chatbot
    categories.value = result.categories
    name.value = bot.bot_name || ''
    category.value = bot.category_id == null ? '' : String(bot.category_id)
    price.value = bot.price == null ? '' : String(bot.price)
    description.value = bot.description || ''
    thumbnail.value = bot.thumbnail_url || null
    isListed.value = Boolean(bot.is_listed)
  } catch (error) {
    loadError.value = apiErrorMessage(error, '出品情報の読み込みに失敗しました。')
  } finally {
    loading.value = false
  }
}

function openPicker() {
  fileInputRef.value?.click()
}

function readThumbnail(file) {
  formError.value = ''
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    formError.value = 'サムネイル画像はJPEG、PNG、WebP形式で指定してください。'
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    formError.value = 'サムネイル画像は5MB以内にしてください。'
    return
  }
  thumbnailFile.value = file
  const reader = new FileReader()
  reader.onload = () => {
    thumbnail.value = reader.result
  }
  reader.readAsDataURL(file)
}

function handleFileChange(e) {
  readThumbnail(e.target.files?.[0])
  e.target.value = ''
}

function handleDrop(e) {
  dragOver.value = false
  readThumbnail(e.dataTransfer.files?.[0])
}

function handlePriceInput(e) {
  price.value = e.target.value.replace(/[^0-9]/g, '').replace(/^0+/, '')
}

function openPreview() {
  formError.value = ''
  if (canSubmit.value && !submitting.value) previewOpen.value = true
}

function closePreview() {
  previewOpen.value = false
}

async function confirmPublish() {
  if (!canSubmit.value || submitting.value) return

  const wasListed = isListed.value
  submitting.value = true
  formError.value = ''
  const body = new FormData()
  body.append('bot_name', name.value.trim())
  body.append('category_id', category.value)
  body.append('price', price.value)
  body.append('description', description.value.trim())
  if (thumbnailFile.value) body.append('thumbnail', thumbnailFile.value)

  try {
    await $fetch(`/api/listings/${chatbotId.value}`, {
      baseURL: config.public.apiBase,
      method: 'PUT',
      credentials: 'include',
      body,
    })
    previewOpen.value = false
    completionMode.value = wasListed ? 'update' : 'publish'
    isListed.value = true
    published.value = true
  } catch (error) {
    formError.value = apiErrorMessage(error, '出品に失敗しました。')
  } finally {
    submitting.value = false
  }
}

function createAnotherBot() {
  navigateTo('/chatbot/creation')
}

onMounted(loadListing)
</script>
