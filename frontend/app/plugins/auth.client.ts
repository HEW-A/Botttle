// アプリ起動時にCookieのaccess_tokenからログイン状態を復元する
export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()
  await authStore.fetchMe()
})
