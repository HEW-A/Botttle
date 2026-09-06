// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },
  // WindowsではlocalhostがIPv6(::1)にのみバインドされることがあり、
  // backend(127.0.0.1)とホスト名を揃えるためにIPv4を明示する
  devServer: {
    host: '127.0.0.1',
  },
  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],
  runtimeConfig: {
    public: {
      // 環境変数 NUXT_PUBLIC_API_BASE で上書き可能
      // Cookie(SameSite=Lax)を使う認証の都合上、backendと同じホスト名(127.0.0.1)に揃える
      apiBase: 'http://127.0.0.1:5000',
    },
  },
  routeRules: {
    // /register ページは作成せず、/login の新規登録タブに統合しているため
    '/register': { redirect: '/login?tab=register' },
  },
})
