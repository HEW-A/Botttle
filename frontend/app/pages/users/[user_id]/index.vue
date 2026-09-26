<template>
  <div class="font-['M_PLUS_1_Code']">
    <div v-if="profile" class="mx-auto flex max-w-4xl flex-col gap-6 px-4 py-8 md:px-6">
      <section class="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(120px,176px)_1fr]">
        <div class="flex aspect-square items-center justify-center rounded-lg border border-slate-300 bg-slate-100">
          <span class="text-5xl font-bold text-slate-700">{{ initial }}</span>
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
        <div class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5">
          <span class="text-sm font-bold text-slate-900">作成品・出品中</span>
          <span class="text-xs text-slate-500">出品中 {{ profile.stats.listed_count }}件</span>
        </div>
        <div class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5">
          <span class="text-sm font-bold text-slate-900">出品履歴</span>
          <span class="text-xs text-slate-500">販売済 {{ profile.stats.sold_count }}件</span>
        </div>
        <div v-if="profile.is_self" class="flex flex-col gap-2 rounded-lg border border-slate-300 p-5">
          <span class="text-sm font-bold text-slate-900">購入履歴</span>
          <span class="text-xs text-slate-500">購入したボット {{ profile.purchase_count }}件</span>
        </div>
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
        <div class="flex flex-col gap-1.5 px-6 pb-5">
          <div class="flex h-1.5 overflow-hidden rounded-sm bg-slate-200">
            <div class="bg-blue-600" :style="{ width: winRateBarWidth }"></div>
          </div>
          <div class="flex justify-between text-[11px] text-slate-500">
            <span>WIN {{ profile.stats.wins }}</span>
            <span>LOSE {{ profile.stats.losses }}</span>
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
            class="h-10 rounded-md bg-blue-600 px-5 text-sm font-medium text-white hover:bg-blue-700"
            @click="save"
          >
            保存する
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// バックエンドAPIは未実装のため、ユーザーが誰であっても同じモックデータを表示する
// (デザインのデフォルト状態=本人ビューを踏襲。実データ連携は別途行う)
const USER_ID_FORMAT_RE = /^[A-Za-z0-9][A-Za-z0-9_]{2,19}$/

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userIdParam = route.params.user_id

if (!USER_ID_FORMAT_RE.test(userIdParam)) {
  throw createError({ statusCode: 404, statusMessage: 'ユーザーが見つかりません' })
}

const profile = ref({
  user_id: userIdParam,
  username: 'Testman',
  developer_profile:
    '会話型ボットを中心に制作しています。BotArenaではロジック対戦系が得意。\n業務効率化・英会話練習向けのボットを出品中です。',
  profile_image_url: null,
  created_at: '2025-04-12T00:00:00+00:00',
  is_self: true,
  stats: { listed_count: 5, sold_count: 23, wins: 128, losses: 54 },
  purchase_count: 9,
  coin_balance: 12480,
})

useHead({
  title: `${profile.value.username} | botttle`,
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

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

const winRateBarWidth = computed(() => {
  const { wins, losses } = profile.value.stats
  const total = wins + losses
  return total === 0 ? '0%' : `${(wins / total) * 100}%`
})

const editing = ref(false)
const draftUsername = ref('')
const draftBio = ref('')
const editError = ref('')

function openEdit() {
  draftUsername.value = profile.value.username
  draftBio.value = profile.value.developer_profile || ''
  editError.value = ''
  editing.value = true
}

function closeEdit() {
  editing.value = false
}

// バックエンド未実装のため、保存は画面上のモックデータを書き換えるだけ
function save() {
  editError.value = ''
  const username = draftUsername.value.trim()
  if (!username) {
    editError.value = '表示名を入力してください'
    return
  }

  profile.value.username = username
  profile.value.developer_profile = draftBio.value
  editing.value = false
}

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
