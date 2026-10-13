// 未ログインの場合は /login へリダイレクトする
// ログイン状態はplugins/auth.tsでSSR時にも復元されるため、サーバー側でも判定してページ内容が一瞬表示されるのを防ぐ
export default defineNuxtRouteMiddleware(() => {
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
    return navigateTo('/login')
  }
})
