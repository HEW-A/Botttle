// 未ログインの場合は /login へリダイレクトする
// ログイン状態の復元(auth.client.ts)はクライアント側のみのため、サーバー側では判定しない
export default defineNuxtRouteMiddleware(() => {
  if (import.meta.server) return

  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
    return navigateTo('/login')
  }
})
