<template>
  <header class="sticky top-0 z-50 border-b border-slate-200 bg-white">
    <nav class="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 md:px-6">
      <NuxtLink to="/main" class="text-2xl tracking-wide text-slate-900">
        botttle
      </NuxtLink>

      <div v-if="!hideRanking || isLoggedIn" class="hidden items-center gap-4 md:flex">
        <NuxtLink v-if="!hideRanking" to="/ranking" class="text-sm whitespace-nowrap text-slate-700 transition-colors hover:text-primary">ランキング</NuxtLink>
        <template v-if="isLoggedIn">
          <NuxtLink to="/botarena" class="text-sm whitespace-nowrap text-slate-700 transition-colors hover:text-primary">BotArena</NuxtLink>
          <NuxtLink to="/chatbot/creation" class="text-sm whitespace-nowrap text-slate-700 transition-colors hover:text-primary">ボットを作成する</NuxtLink>
          <NuxtLink :to="myCreatedPath" class="text-sm whitespace-nowrap text-slate-700 transition-colors hover:text-primary">出品する</NuxtLink>
        </template>
      </div>

      <form v-if="!hideSearch" class="ml-auto hidden w-64 flex-none md:block" role="search" @submit.prevent="handleSearch">
        <UInput v-model="searchQuery" class="w-full" placeholder="Botを検索" aria-label="Botを検索" :ui="{ base: 'pe-11' }">
          <template #trailing>
            <UButton type="submit" variant="ghost" size="sm" square aria-label="検索" class="size-8 justify-center px-0">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="M21 21l-4.3-4.3"></path>
              </svg>
            </UButton>
          </template>
        </UInput>
      </form>

      <div class="hidden items-center gap-2 md:flex" :class="{ 'ml-auto': hideSearch }">
        <template v-if="isLoggedIn">
          <UButton to="/cart" color="neutral" variant="ghost" square aria-label="カート" class="size-10 justify-center px-0 hover:text-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="9" cy="20" r="1"></circle>
              <circle cx="18" cy="20" r="1"></circle>
              <path d="M2 3h3l2.7 12.4a1 1 0 0 0 1 .8h9.6a1 1 0 0 0 1-.8L21 7H6"></path>
            </svg>
          </UButton>
          <UButton :to="myFavoritePath" color="neutral" variant="ghost" square aria-label="お気に入り" class="size-10 justify-center px-0 hover:text-primary">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3z"></path>
            </svg>
          </UButton>
          <UButton
            variant="soft"
            aria-label="アカウント"
            class="size-10 justify-center rounded-full bg-primary-100 px-0 text-primary-700 hover:bg-primary-200"
            @click="accountModalOpen = true"
          >
            {{ userInitial }}
          </UButton>
        </template>
        <template v-else>
          <UButton to="/login" variant="ghost">ログイン</UButton>
          <UButton to="/login?tab=register">新規会員登録</UButton>
        </template>
      </div>

      <UButton
        color="neutral"
        variant="ghost"
        square
        :aria-label="mobileMenuOpen ? 'メニューを閉じる' : 'メニューを開く'"
        :aria-expanded="mobileMenuOpen"
        class="ml-auto size-10 justify-center px-0 md:hidden"
        @click="mobileMenuOpen = !mobileMenuOpen"
      >
        <svg v-if="mobileMenuOpen" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18 6L6 18"></path>
          <path d="M6 6l12 12"></path>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 7h16"></path>
          <path d="M4 12h16"></path>
          <path d="M4 17h16"></path>
        </svg>
      </UButton>
    </nav>

    <div v-if="mobileMenuOpen" class="sticky top-16 z-40 flex flex-col gap-1 border-b border-slate-200 bg-white px-4 py-4 md:hidden">
      <form v-if="!hideSearch" class="mb-2" role="search" @submit.prevent="handleSearch">
        <UInput v-model="searchQuery" class="w-full" placeholder="Botを検索" aria-label="Botを検索" :ui="{ base: 'pe-11' }">
          <template #trailing>
            <UButton type="submit" variant="ghost" size="sm" square aria-label="検索" class="size-8 justify-center px-0">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7"></circle>
                <path d="M21 21l-4.3-4.3"></path>
              </svg>
            </UButton>
          </template>
        </UInput>
      </form>

      <NuxtLink v-if="!hideRanking" to="/ranking" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">ランキング</NuxtLink>
      <template v-if="isLoggedIn">
        <NuxtLink to="/botarena" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">BotArena</NuxtLink>
        <NuxtLink to="/chatbot/creation" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">ボットを作成する</NuxtLink>
        <NuxtLink :to="myCreatedPath" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">出品する</NuxtLink>
      </template>

      <div class="my-2 h-px bg-slate-200"></div>

      <template v-if="isLoggedIn">
        <NuxtLink to="/cart" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">カート</NuxtLink>
        <NuxtLink :to="myFavoritePath" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">お気に入り</NuxtLink>
        <button type="button" class="px-1 py-2 text-left text-sm text-slate-700" @click="openAccountModal">
          マイページ
        </button>
      </template>
      <div v-else class="flex gap-2 p-1">
        <UButton to="/login" variant="outline" class="flex-1 justify-center" @click="closeMobileMenu">ログイン</UButton>
        <UButton to="/login?tab=register" class="flex-1 justify-center" @click="closeMobileMenu">新規会員登録</UButton>
      </div>
    </div>

    <!-- アカウント -->
    <UModal v-model:open="accountModalOpen" title="アカウント" :ui="{ content: 'sm:max-w-xs' }">
      <template #content>
        <div class="relative flex flex-col gap-5 px-8 py-9">
          <UButton
            color="neutral"
            variant="ghost"
            size="sm"
            square
            aria-label="閉じる"
            class="absolute top-3 right-3"
            @click="accountModalOpen = false"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </UButton>

          <div class="flex flex-col items-center gap-2 text-center">
            <div class="flex size-14 items-center justify-center rounded-full bg-primary-100 text-lg font-bold text-primary-700" aria-hidden="true">
              {{ userInitial }}
            </div>
            <p class="text-base font-bold text-slate-900">{{ authUser?.username }}</p>
          </div>

          <UButton :to="myProfilePath" variant="outline" block @click="accountModalOpen = false">マイページ</UButton>
          <UButton block :disabled="logoutLoading" @click="handleLogout">
            {{ logoutLoading ? 'ログアウト中...' : 'ログアウト' }}
          </UButton>
        </div>
      </template>
    </UModal>
  </header>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{ forceGuest?: boolean; hideSearch?: boolean; hideRanking?: boolean }>(),
  {
    forceGuest: false,
    hideSearch: false,
    hideRanking: false,
  },
)

const authStore = useAuthStore()
const { isLoggedIn: isLoggedInState, user: authUser } = storeToRefs(authStore)
const isLoggedIn = computed(() => isLoggedInState.value && !props.forceGuest)
const myProfilePath = computed(() => (authUser.value ? `/users/${authUser.value.user_id}` : '/login'))
const myCreatedPath = computed(() => (authUser.value ? `${myProfilePath.value}/created` : '/login'))
const myFavoritePath = computed(() => (authUser.value ? `${myProfilePath.value}/favorite` : '/login'))
// アカウントのボタンに出す文字(ユーザー名の頭文字)
const userInitial = computed(() => (authUser.value?.username || '?').trim().charAt(0).toUpperCase())

const router = useRouter()
const accountModalOpen = ref(false)
const logoutLoading = ref(false)

function openAccountModal() {
  closeMobileMenu()
  accountModalOpen.value = true
}

async function handleLogout() {
  logoutLoading.value = true
  try {
    await authStore.logout()
  } finally {
    logoutLoading.value = false
    accountModalOpen.value = false
    router.push('/')
  }
}

const mobileMenuOpen = ref(false)
const searchQuery = ref('')

// 検索APIが未実装のため、現時点ではクエリの送信は行わずメニューを閉じるのみ
function handleSearch() {
  closeMobileMenu()
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}
</script>
