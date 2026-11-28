<template>
  <CommonPageContainer v-if="profile" class="flex flex-col gap-6">
    <section class="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(120px,176px)_1fr]">
      <div class="flex aspect-square items-center justify-center border border-slate-200 bg-primary-100" aria-hidden="true">
        <span class="text-5xl font-bold text-primary-700">{{ initial }}</span>
      </div>
      <UCard :ui="{ body: 'flex flex-col gap-3 px-6 py-5 sm:px-6 sm:py-5' }">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex min-w-0 flex-col gap-1">
            <h1 class="text-2xl font-bold text-slate-900">{{ profile.username }}</h1>
            <span class="text-xs text-slate-500">@{{ profile.user_id }} ・ {{ memberSinceLabel }}</span>
          </div>
          <UButton v-if="profile.is_self" variant="outline" class="flex-none" @click="openEdit">プロフィールを編集</UButton>
        </div>
        <p class="text-sm leading-loose whitespace-pre-wrap text-slate-700">
          {{ profile.developer_profile || '自己紹介はまだ登録されていません。' }}
        </p>
      </UCard>
    </section>

    <section class="grid grid-cols-1 gap-4 sm:grid-cols-2" :class="{ 'lg:grid-cols-3': profile.is_self }">
      <NuxtLink :to="`/users/${profile.user_id}/created`" class="flex flex-col gap-2 border border-slate-200 bg-white p-5 transition-colors hover:border-primary">
        <span class="text-sm font-bold text-slate-900">作成品・出品中</span>
        <span class="text-xs text-slate-500">出品中 {{ profile.stats.listed_count }}件</span>
      </NuxtLink>
      <NuxtLink :to="`/users/${profile.user_id}/sales-history`" class="flex flex-col gap-2 border border-slate-200 bg-white p-5 transition-colors hover:border-primary">
        <span class="text-sm font-bold text-slate-900">出品履歴</span>
        <span class="text-xs text-slate-500">販売済 {{ profile.stats.sold_count }}件</span>
      </NuxtLink>
      <NuxtLink
        v-if="profile.is_self"
        :to="`/users/${profile.user_id}/purchase-history`"
        class="flex flex-col gap-2 border border-slate-200 bg-white p-5 transition-colors hover:border-primary"
      >
        <span class="text-sm font-bold text-slate-900">購入履歴</span>
        <span class="text-xs text-slate-500">購入したボット {{ profile.purchase_count }}件</span>
      </NuxtLink>
    </section>

    <UCard as="section" :ui="{ header: 'flex items-center justify-between px-6 py-3.5 sm:px-6', body: 'p-0 sm:p-0' }">
      <template #header>
        <CommonSectionTitle>戦績サマリー</CommonSectionTitle>
        <span class="text-xs text-slate-500">BotArena 通算</span>
      </template>
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
          <span class="text-3xl font-bold text-primary">
            {{ winRateLabel }}<span v-if="winRateLabel !== '-'" class="ml-0.5 text-base">%</span>
          </span>
        </div>
        <div v-if="profile.is_self" class="flex flex-col gap-1.5 px-6 py-5">
          <span class="text-xs text-slate-500">所持コイン</span>
          <span class="text-3xl font-bold text-slate-900">
            {{ profile.coin_balance.toLocaleString() }}<span class="ml-1 text-sm font-normal text-slate-500">BC</span>
          </span>
        </div>
      </div>
    </UCard>

    <div v-if="profile.is_self" class="flex justify-center pt-2">
      <UButton block variant="outline" class="max-w-80" @click="handleLogout">ログアウト</UButton>
    </div>

    <UModal
      v-model:open="editing"
      title="プロフィールを編集"
      description="表示名と自己紹介を変更できます。"
      :ui="{ footer: 'justify-end' }"
    >
      <!-- 閉じるボタンの既定のアイコンは外部(Iconify)から取得するため、SVG を直接描く -->
      <template #close>
        <UButton color="neutral" variant="ghost" size="sm" square aria-label="閉じる" class="absolute top-4 right-4">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </UButton>
      </template>

      <template #body>
        <form id="profile-edit-form" class="flex flex-col gap-4" @submit.prevent="save">
          <div class="flex flex-col gap-1.5">
            <label for="profile-username" class="text-xs font-bold text-slate-700">表示名</label>
            <UInput id="profile-username" v-model="draftUsername" class="w-full" :maxlength="20" autocomplete="nickname" />
          </div>
          <div class="flex flex-col gap-1.5">
            <label for="profile-bio" class="text-xs font-bold text-slate-700">自己紹介</label>
            <UTextarea id="profile-bio" v-model="draftBio" class="w-full" :rows="4" :maxlength="160" />
            <span class="self-end text-xs text-slate-500">{{ draftBio.length }} / 160</span>
          </div>
          <p v-if="editError" class="text-sm text-red-600">{{ editError }}</p>
        </form>
      </template>

      <template #footer>
        <UButton variant="ghost" @click="closeEdit">キャンセル</UButton>
        <UButton type="submit" form="profile-edit-form">保存する</UButton>
      </template>
    </UModal>
  </CommonPageContainer>
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
  router.push('/')
}
</script>
