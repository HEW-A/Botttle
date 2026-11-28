<template>
  <div class="font-['M_PLUS_1_Code']">
    <div v-if="loading" class="mx-auto max-w-4xl px-4 py-16 text-center text-sm text-slate-500">
      プロフィールを読み込んでいます…
    </div>

    <div v-else-if="loadError" class="mx-auto max-w-4xl px-4 py-16 text-center">
      <p class="text-sm text-red-600">{{ loadError }}</p>
      <button
        type="button"
        class="mt-4 rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
        @click="loadProfile"
      >
        再読み込み
      </button>
    </div>

    <div v-else-if="profile" class="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8 md:px-6">
      <section class="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(120px,176px)_1fr]">
        <div class="flex aspect-square items-center justify-center rounded-lg border border-slate-300 bg-slate-100">
          <img
            v-if="profile.profile_image_url"
            :src="profile.profile_image_url"
            :alt="`${profile.username}のプロフィール画像`"
            class="h-full w-full rounded-lg object-cover"
          />
          <span v-else class="text-5xl font-bold text-slate-700">{{ initial }}</span>
        </div>
        <div class="flex flex-col gap-3 rounded-lg border border-slate-300 px-6 py-5">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div class="flex min-w-0 flex-col gap-1">
              <h1 class="text-2xl font-bold text-slate-900">{{ profile.username }}</h1>
              <span class="text-xs text-slate-500">@{{ profile.user_id }} ・ {{ memberSinceLabel }}</span>
            </div>
            <button
              v-if="profile.is_self"
              type="button"
              class="flex-none rounded-md border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50"
              @click="openEdit"
            >
              プロフィールを編集
            </button>
          </div>
          <p class="text-sm leading-loose whitespace-pre-wrap text-slate-700">
            {{ profile.developer_profile || '自己紹介はまだ登録されていません。' }}
          </p>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-4 sm:grid-cols-2" :class="{ 'lg:grid-cols-3': profile.is_self }">
        <NuxtLink :to="`/users/${profile.user_id}/created`" class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5 hover:bg-slate-50">
          <span class="text-sm font-bold text-slate-900">作成品・出品中</span>
          <span class="text-xs text-slate-500">出品中 {{ profile.stats.listed_count }}件</span>
        </NuxtLink>
        <NuxtLink :to="`/users/${profile.user_id}/sales-history`" class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5 hover:bg-slate-50">
          <span class="text-sm font-bold text-slate-900">出品履歴</span>
          <span class="text-xs text-slate-500">販売済 {{ profile.stats.sold_count }}件</span>
        </NuxtLink>
        <NuxtLink v-if="profile.is_self" :to="`/users/${profile.user_id}/purchase-history`" class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5 hover:bg-slate-50">
          <span class="text-sm font-bold text-slate-900">購入履歴</span>
          <span class="text-xs text-slate-500">購入したボット {{ profile.purchase_count }}件</span>
        </NuxtLink>
      </section>

      <section class="rounded-lg border border-slate-300">
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-3.5">
          <h2 class="text-[15px] font-bold text-slate-700">戦績サマリー</h2>
          <span class="text-xs text-slate-500">BotArena 通算</span>
        </div>
        <div class="grid grid-cols-2" :class="profile.is_self ? 'sm:grid-cols-4' : 'sm:grid-cols-3'">
          <div class="flex flex-col gap-1.5 border-r border-slate-200 px-6 py-5">
            <span class="text-xs text-slate-500">勝利数</span>
            <span class="text-3xl font-bold text-slate-900">{{ profile.stats.wins }}</span>
          </div>
          <div class="flex flex-col gap-1.5 border-r border-slate-200 px-6 py-5">
            <span class="text-xs text-slate-500">敗北数</span>
            <span class="text-3xl font-bold text-slate-900">{{ profile.stats.losses }}</span>
          </div>
          <div
            class="flex flex-col gap-1.5 px-6 py-5"
            :class="{ 'border-r border-slate-200': profile.is_self }"
          >
            <span class="text-xs text-slate-500">勝率</span>
            <span class="text-3xl font-bold text-blue-600">
              {{ winRateLabel }}<span v-if="winRateLabel !== '-'" class="ml-0.5 text-base">%</span>
            </span>
          </div>
          <div v-if="profile.is_self" class="flex flex-col gap-1.5 px-6 py-5">
            <span class="text-xs text-slate-500">所持コイン</span>
            <span class="text-3xl font-bold text-slate-900">
              {{ profile.coin_balance.toLocaleString() }}<span class="ml-1 text-sm font-medium text-slate-500">BC</span>
            </span>
          </div>
        </div>
      </section>

      <div v-if="profile.is_self" class="flex justify-center pt-2">
        <button
          type="button"
          class="w-full max-w-[320px] rounded-md border border-slate-700 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-700 hover:text-white"
          @click="handleLogout"
        >
          ログアウト
        </button>
      </div>
    </div>

    <div
      v-if="editing"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/45 px-4"
      @click="closeEdit"
    >
      <div class="flex w-full max-w-[480px] flex-col rounded-lg border border-slate-300 bg-white" @click.stop>
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-4">
          <h2 class="text-base font-bold text-slate-700">プロフィールを編集</h2>
          <button type="button" aria-label="閉じる" class="text-slate-500 hover:text-slate-800" @click="closeEdit">
            ✕
          </button>
        </div>
        <div class="flex flex-col gap-4 px-6 py-5">
          <label class="flex flex-col gap-1.5 text-xs font-medium text-slate-700">
            表示名
            <input
              v-model="draftUsername"
              type="text"
              maxlength="20"
              class="h-10 rounded-md border border-slate-300 px-3 text-sm text-slate-900 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
            />
          </label>
          <label class="flex flex-col gap-1.5 text-xs font-medium text-slate-700">
            自己紹介
            <textarea
              v-model="draftBio"
              rows="4"
              maxlength="160"
              class="rounded-md border border-slate-300 px-3 py-2.5 text-sm leading-relaxed text-slate-900 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
            ></textarea>
            <span class="self-end text-[11px] font-normal text-slate-500">{{ draftBio.length }} / 160</span>
          </label>
          <p v-if="editError" class="text-sm text-red-500">{{ editError }}</p>
        </div>
        <div class="flex justify-end gap-2.5 border-t border-slate-200 px-6 py-3.5">
          <button
            type="button"
            class="h-10 rounded-md border border-slate-300 px-4 text-sm text-slate-700 hover:bg-slate-100"
            @click="closeEdit"
          >
            キャンセル
          </button>
          <button
            type="button"
            :disabled="saving"
            class="h-10 rounded-md bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            @click="save"
          >
            {{ saving ? '保存中…' : '保存する' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const USER_ID_FORMAT_RE = /^[A-Za-z0-9][A-Za-z0-9_]{2,19}$/

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const config = useRuntimeConfig()

const userIdParam = computed(() => String(route.params.user_id))

if (!USER_ID_FORMAT_RE.test(userIdParam.value)) {
  throw createError({ statusCode: 404, statusMessage: 'ユーザーが見つかりません' })
}

const profile = ref(null)
const loading = ref(true)
const loadError = ref('')

useHead(() => ({
  title: profile.value ? `${profile.value.username} | botttle` : 'ユーザープロフィール | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
}))

const initial = computed(() => (profile.value?.username || '?').trim().charAt(0).toUpperCase())

const memberSinceLabel = computed(() => {
  const date = new Date(profile.value.created_at)
  return `${date.getFullYear()}年${date.getMonth() + 1}月から利用`
})

const winRateLabel = computed(() => {
  const { wins, losses } = profile.value.stats
  const total = wins + losses
  return total === 0 ? '-' : ((wins / total) * 100).toFixed(1)
})

const editing = ref(false)
const draftUsername = ref('')
const draftBio = ref('')
const editError = ref('')
const saving = ref(false)

function apiErrorMessage(error, fallback) {
  return error?.data?.error || fallback
}

async function loadProfile() {
  loading.value = true
  loadError.value = ''
  profile.value = null
  try {
    profile.value = await $fetch(`/api/users/${userIdParam.value}`, {
      baseURL: config.public.apiBase,
      credentials: 'include',
    })
  } catch (error) {
    if (error?.statusCode === 404 || error?.status === 404) {
      showError({ statusCode: 404, statusMessage: 'ユーザーが見つかりません' })
      return
    }
    loadError.value = apiErrorMessage(error, 'プロフィールの読み込みに失敗しました。')
  } finally {
    loading.value = false
  }
}

function openEdit() {
  draftUsername.value = profile.value.username
  draftBio.value = profile.value.developer_profile || ''
  editError.value = ''
  editing.value = true
}

function closeEdit() {
  editing.value = false
}

async function save() {
  if (saving.value) return
  editError.value = ''
  const username = draftUsername.value.trim()
  if (!username) {
    editError.value = '表示名を入力してください'
    return
  }

  saving.value = true
  try {
    const result = await $fetch(`/api/users/${userIdParam.value}`, {
      baseURL: config.public.apiBase,
      method: 'PATCH',
      credentials: 'include',
      body: {
        username,
        developer_profile: draftBio.value,
      },
    })
    profile.value.username = result.username
    profile.value.developer_profile = result.developer_profile
    await authStore.fetchMe()
    editing.value = false
  } catch (error) {
    editError.value = apiErrorMessage(error, 'プロフィールの保存に失敗しました。')
  } finally {
    saving.value = false
  }
}

async function handleLogout() {
  await authStore.logout()
  router.push('/')
}

onMounted(loadProfile)

watch(userIdParam, (value) => {
  if (!USER_ID_FORMAT_RE.test(value)) {
    showError({ statusCode: 404, statusMessage: 'ユーザーが見つかりません' })
    return
  }
  editing.value = false
  loadProfile()
})
</script>
