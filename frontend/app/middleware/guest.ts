// ログイン中のユーザーがログイン画面に直接アクセスした場合、メイン画面へリダイレクトする
export default defineNuxtRouteMiddleware(() => {
  const { isLoggedIn } = storeToRefs(useAuthStore())

  if (isLoggedIn.value) {
    return navigateTo('/main')
  }
})
