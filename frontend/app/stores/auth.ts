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
    await $fetch('/api/auth/login', {
      baseURL: apiBase(),
      method: 'POST',
      credentials: 'include',
      body: { user_id: userId, password },
    })
    await fetchMe()
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
  async function fetchMe() {
    try {
      user.value = await $fetch<AuthUser>('/api/auth/me', {
        baseURL: apiBase(),
        credentials: 'include',
      })
    } catch {
      user.value = null
    }
  }

  return { user, isLoggedIn, login, signup, logout, fetchMe }
})
