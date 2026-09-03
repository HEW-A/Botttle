// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      // 環境変数 NUXT_PUBLIC_API_BASE で上書き可能
      apiBase: 'http://localhost:5000',
    },
  },
  routeRules: {
    // /register ページは作成せず、/login の新規登録タブに統合しているため
    '/register': { redirect: '/login?tab=register' },
  },
})
