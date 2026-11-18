<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <main class="flex-1">
      <div class="mx-auto flex w-full max-w-[640px] flex-col px-6 py-14">
        <div v-if="loading" class="border-2 border-slate-900 bg-white px-8 py-16 text-center text-sm text-slate-500">
          出品情報を読み込んでいます…
        </div>

        <div v-else-if="loadError" class="flex flex-col items-center gap-4 border-2 border-red-300 bg-white px-8 py-16 text-center">
          <p class="text-sm font-bold text-red-600">{{ loadError }}</p>
          <NuxtLink to="/chatbot/creation" class="border-2 border-slate-700 bg-white px-7 py-3 text-sm font-bold text-slate-700">
            Bot作成画面へ戻る
          </NuxtLink>
        </div>

        <div v-else-if="published" class="flex flex-col items-center gap-5 border-2 border-slate-900 bg-white px-8 py-16 text-center">
          <div class="flex h-14 w-14 items-center justify-center rounded-full border-2 border-blue-600">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 6L9 17l-5-5"></path>
            </svg>
          </div>
          <div class="flex flex-col gap-2">
            <h2 class="text-xl font-bold text-slate-900">出品が完了しました</h2>
            <p class="text-sm text-slate-500">「{{ name }}」をマーケットに公開しました。</p>
          </div>
          <div class="flex flex-wrap justify-center gap-3">
            <NuxtLink :to="`/chatbot/${chatbotId}`" class="border-2 border-blue-600 bg-blue-600 px-7 py-3 text-sm font-bold text-white">
              出品したボットを確認
            </NuxtLink>
            <button type="button" class="border-2 border-slate-700 bg-white px-7 py-3 text-sm font-bold text-slate-700" @click="createAnotherBot">
              続けて出品する
            </button>
          </div>
        </div>

        <div v-else class="flex flex-col gap-9">
          <div class="flex flex-col gap-1.5">
            <h1 class="text-2xl font-bold text-slate-900">チャットボットを出品する</h1>
            <p class="text-sm leading-relaxed text-slate-500">必要事項を入力して、マーケットに公開しましょう。</p>
          </div>

          <div class="flex flex-col gap-6 border-2 border-slate-900 bg-white p-8">
            <div class="flex items-start gap-4">
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="hidden"
                @change="handleFileChange"
              />
              <div
                class="flex h-28 w-28 flex-none cursor-pointer flex-col items-center justify-center overflow-hidden border-2 border-dashed"
                :class="dragOver ? 'border-blue-600 bg-blue-50' : 'border-slate-300 bg-slate-50'"
                @click="openPicker"
                @drop.prevent="handleDrop"
                @dragover.prevent="dragOver = true"
                @dragleave="dragOver = false"
              >
                <img v-if="thumbnail" :src="thumbnail" alt="サムネイルのプレビュー" class="h-full w-full object-cover" />
                <template v-else>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="6" width="18" height="14" rx="0"></rect>
                    <circle cx="12" cy="13" r="3.5"></circle>
                    <path d="M8 6l1.2-2h5.6L16 6"></path>
                  </svg>
                  <span class="mt-1.5 text-[11px] text-slate-400">画像を追加</span>
                </template>
              </div>
              <p class="pt-1.5 text-[12.5px] leading-relaxed text-slate-500">
                ボットのロゴやチャット画面のスクリーンショットがあると購入されやすくなります。
                <span class="mt-1 block">JPEG・PNG・WebP、5MB以内</span>
              </p>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[12.5px] font-bold text-slate-700">商品名</label>
              <input
                v-model="name"
                type="text"
                maxlength="40"
                placeholder="例: 領収書仕分けボット"
                class="w-full border border-slate-300 px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[12.5px] font-bold text-slate-700">カテゴリ</label>
              <select
                v-model="category"
                class="w-full border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
              >
                <option value="">選択してください</option>
                <option v-for="c in categories" :key="c.category_id" :value="String(c.category_id)">{{ c.category_name }}</option>
              </select>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[12.5px] font-bold text-slate-700">販売価格</label>
              <div class="flex items-center border border-slate-300 px-3.5 focus-within:border-blue-600 focus-within:outline focus-within:outline-2 focus-within:outline-blue-600">
                <span class="mr-1.5 text-sm text-slate-500">¥</span>
                <input
                  :value="price"
                  type="text"
                  inputmode="numeric"
                  placeholder="0"
                  class="flex-1 border-none bg-transparent py-2.5 text-sm text-slate-900"
                  @input="handlePriceInput"
                />
              </div>
            </div>

            <div class="flex flex-col gap-1.5">
              <label class="text-[12.5px] font-bold text-slate-700">説明文</label>
              <textarea
                v-model="description"
                rows="5"
                maxlength="5000"
                placeholder="どんなことができるボットか、使い方や注意点を書いてください"
                class="w-full resize-y border border-slate-300 px-3.5 py-2.5 text-sm leading-relaxed text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
              ></textarea>
            </div>

            <p v-if="formError" class="text-sm font-bold text-red-600">{{ formError }}</p>

            <button
              type="button"
              class="w-full border-2 border-transparent py-4 text-[15px] font-bold"
              :class="canSubmit && !submitting ? 'cursor-pointer bg-blue-600 text-white' : 'cursor-not-allowed bg-slate-200 text-slate-400'"
              :disabled="!canSubmit || submitting"
              @click="openPreview"
            >
              {{ submitting ? '出品中…' : '出品する' }}
            </button>
          </div>
        </div>
      </div>
    </main>

    <CommonAppFooter />

    <div v-if="previewOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-5">
      <div class="w-full max-w-[420px] border-2 border-slate-900 bg-white">
        <div class="flex h-40 w-full items-center justify-center overflow-hidden bg-slate-100">
          <img v-if="thumbnail" :src="thumbnail" alt="サムネイルのプレビュー" class="h-full w-full object-cover" />
          <svg v-else width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="6" width="18" height="14" rx="0"></rect>
            <circle cx="12" cy="13" r="3.5"></circle>
          </svg>
        </div>
        <div class="flex flex-col gap-2.5 p-6">
          <span class="w-fit bg-blue-100 px-2.5 py-1 text-[11px] font-bold text-blue-800">{{ categoryDisplay }}</span>
          <div class="text-lg font-bold text-slate-900">{{ name }}</div>
          <div class="max-h-20 overflow-auto text-[13px] leading-relaxed text-slate-500">{{ description }}</div>
          <div class="text-xl font-bold text-slate-900">¥{{ priceDisplay }}</div>
          <div class="mt-2.5 flex gap-2.5">
            <button type="button" :disabled="submitting" class="flex-1 border-2 border-slate-700 bg-white py-3 text-sm font-bold text-slate-700 disabled:cursor-not-allowed disabled:text-slate-400" @click="closePreview">
              編集に戻る
            </button>
            <button type="button" :disabled="submitting" class="flex-1 border-2 border-blue-600 bg-blue-600 py-3 text-sm font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300 disabled:border-slate-300" @click="confirmPublish">
              {{ submitting ? '出品中…' : 'この内容で出品する' }}
            </button>
          </div>
          <p v-if="formError" class="text-sm font-bold text-red-600">{{ formError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
  middleware: 'auth',
})

useHead({
  title: 'チャットボットを出品する | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
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
const priceDisplay = computed(() => (price.value ? Number(price.value).toLocaleString() : '0'))
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
  thumbnailFile.value = null
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
  price.value = e.target.value.replace(/[^0-9]/g, '')
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
