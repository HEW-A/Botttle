export interface AuthUser {
  user_id: string
  username: string
  email: string | null
}

// ログイン状態(user, isLoggedIn)と、バックエンドAPIとやり取りする認証アクションをまとめるstore
export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isLoggedIn = computed(() => user.value !== null)

  function apiBase() {
    return useRuntimeConfig().public.apiBase
  }

  async function login(userId: string, password: string) {
    const result = await $fetch<AuthUser>('/api/auth/login', {
      baseURL: apiBase(),
      method: 'POST',
      credentials: 'include',
      body: { user_id: userId, password },
    })
    user.value = {
      user_id: result.user_id,
      username: result.username,
      email: result.email,
    }
  }

  async function signup(userId: string, username: string, password: string, email?: string) {
    await $fetch('/api/auth/signup', {
      baseURL: apiBase(),
      method: 'POST',
      credentials: 'include',
      body: { user_id: userId, username, password, email: email || undefined },
    })
    await fetchMe()
  }

  async function logout() {
    await $fetch('/api/auth/logout', {
      baseURL: apiBase(),
      method: 'POST',
      credentials: 'include',
    })
    user.value = null
  }

  // Cookieのaccess_tokenからログイン状態を復元する(アプリ起動時などに呼ぶ想定)
  // SSR中はブラウザのCookieが自動送信されないため、受信したリクエストのCookieヘッダーを明示的に転送する
  async function fetchMe() {
    try {
      user.value = await $fetch<AuthUser>('/api/auth/me', {
        baseURL: apiBase(),
        credentials: 'include',
        headers: useRequestHeaders(['cookie']),
      })
    } catch {
      user.value = null
    }
  }

  return { user, isLoggedIn, login, signup, logout, fetchMe }
})
