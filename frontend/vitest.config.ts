import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// 注意: Nuxt 4.5 は Vite 8(rolldown)を使うが、Vitest はまだ Vite 8 に非対応のため
// @nuxt/test-utils の nuxt ランタイム環境は利用できない。
// ここでは Vitest 同梱の Vite(7 系, rollup) + @vitejs/plugin-vue で
// SFC をトランスフォームし、Nuxt のコンポーザブルはテスト側でモックする。
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
  },
})
