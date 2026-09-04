<template>
  <header class="sticky top-0 z-50 border-b border-slate-200 bg-white font-['M_PLUS_1_Code']">
    <nav class="mx-auto flex h-16 max-w-7xl items-center gap-6 px-4 md:px-6">
      <NuxtLink to="/main" class="text-lg font-bold text-blue-600">
        Botttle
      </NuxtLink>

      <div class="hidden items-center gap-4 md:flex">
        <a href="#" class="text-sm whitespace-nowrap text-slate-700 hover:text-blue-600">ランキング</a>
        <template v-if="isLoggedIn">
          <a href="#" class="text-sm whitespace-nowrap text-slate-700 hover:text-blue-600">BotArena</a>
          <a href="#" class="text-sm whitespace-nowrap text-slate-700 hover:text-blue-600">ボットを作成する</a>
          <a href="#" class="text-sm whitespace-nowrap text-slate-700 hover:text-blue-600">出品する</a>
        </template>
      </div>

      <form class="relative ml-auto hidden w-64 flex-none md:block" @submit.prevent="handleSearch">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Botを検索"
          class="w-full rounded border border-slate-300 bg-slate-50 py-2 pr-9 pl-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
        />
        <button
          type="submit"
          aria-label="検索"
          class="absolute top-1/2 right-1 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded text-blue-600 hover:bg-blue-50"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7"></circle>
            <path d="M21 21l-4.3-4.3"></path>
          </svg>
        </button>
      </form>

      <div class="hidden items-center gap-2 md:flex">
        <NuxtLink
          v-if="isLoggedIn"
          to="/mypage"
          aria-label="アカウント"
          class="flex h-9 w-9 items-center justify-center rounded bg-slate-700 text-sm font-semibold text-white hover:bg-slate-800"
        >
          U
        </NuxtLink>
        <template v-else>
          <NuxtLink to="/login" class="px-2 py-2 text-sm font-medium whitespace-nowrap text-blue-600 hover:text-blue-700">
            ログイン
          </NuxtLink>
          <NuxtLink
            to="/login?tab=register"
            class="rounded bg-blue-600 px-4 py-2 text-sm font-semibold whitespace-nowrap text-white hover:bg-blue-700"
          >
            新規会員登録
          </NuxtLink>
        </template>
      </div>

      <button
        type="button"
        aria-label="メニュー"
        class="ml-auto flex h-10 w-10 items-center justify-center text-slate-700 md:hidden"
        @click="mobileMenuOpen = !mobileMenuOpen"
      >
        <svg v-if="mobileMenuOpen" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 6L6 18"></path>
          <path d="M6 6l12 12"></path>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 7h16"></path>
          <path d="M4 12h16"></path>
          <path d="M4 17h16"></path>
        </svg>
      </button>
    </nav>

    <div v-if="mobileMenuOpen" class="sticky top-16 z-40 flex flex-col gap-1 border-b border-slate-200 bg-white px-4 py-4 md:hidden">
      <form class="relative mb-2" @submit.prevent="handleSearch">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Botを検索"
          class="w-full rounded border border-slate-300 bg-slate-50 py-2 pr-9 pl-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
        />
        <button
          type="submit"
          aria-label="検索"
          class="absolute top-1/2 right-1 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded text-blue-600 hover:bg-blue-50"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7"></circle>
            <path d="M21 21l-4.3-4.3"></path>
          </svg>
        </button>
      </form>

      <a href="#" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">ランキング</a>
      <template v-if="isLoggedIn">
        <a href="#" class="px-1 py-2 text-sm text-blue-600" @click="closeMobileMenu">BotArena</a>
        <a href="#" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">ボットを作成する</a>
        <a href="#" class="px-1 py-2 text-sm text-slate-700" @click="closeMobileMenu">出品する</a>
      </template>

      <div class="my-2 h-px bg-slate-200"></div>

      <NuxtLink
        v-if="isLoggedIn"
        to="/mypage"
        class="px-1 py-2 text-sm font-medium text-slate-700"
        @click="closeMobileMenu"
      >
        マイページ
      </NuxtLink>
      <div v-else class="flex gap-2 p-1">
        <NuxtLink
          to="/login"
          class="flex-1 rounded border border-slate-300 py-2.5 text-center text-sm font-medium text-slate-700"
          @click="closeMobileMenu"
        >
          ログイン
        </NuxtLink>
        <NuxtLink
          to="/login?tab=register"
          class="flex-1 rounded bg-blue-600 py-2.5 text-center text-sm font-semibold text-white"
          @click="closeMobileMenu"
        >
          新規会員登録
        </NuxtLink>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
const { isLoggedIn } = storeToRefs(useAuthStore())

useHead({
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

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
