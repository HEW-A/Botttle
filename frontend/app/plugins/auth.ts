// アプリ起動時にCookieのaccess_tokenからログイン状態を復元する
// SSR側でも実行することで、リロード直後の最初のHTMLからログイン状態を正しく反映させる
export default defineNuxtPlugin(async () => {
  const authStore = useAuthStore()
  await authStore.fetchMe()
})
