import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount } from '@vue/test-utils'
import App from './app.vue'

// app.vue は Nuxt のコンポーザブル(useRuntimeConfig / useFetch)を auto-import 前提で使う。
// ここでは Nuxt ランタイムを起動せず、これらをグローバルにモックして検証する。
const useFetchMock = vi.fn()

vi.stubGlobal('useRuntimeConfig', () => ({
  public: { apiBase: 'http://localhost:5000' },
}))
vi.stubGlobal('useFetch', useFetchMock)

// Nuxt 提供コンポーネントは中身を持たないスタブに差し替える
const mountApp = () =>
  mount(App, {
    global: {
      stubs: {
        NuxtRouteAnnouncer: true,
        NuxtPage: true,
      },
    },
  })

describe('app.vue（backend 疎通表示）', () => {
  beforeEach(() => {
    useFetchMock.mockReset()
  })

  it('backend が正常応答した場合、"ok" を含む文言が表示される', () => {
    useFetchMock.mockReturnValue({
      data: ref({ status: 'ok' }),
      error: ref(null),
    })

    const wrapper = mountApp()

    expect(wrapper.get('[data-testid="backend-status"]').text()).toContain('ok')
  })

  it('backend が応答しない(fetch 失敗)場合、エラー表示がされる', () => {
    useFetchMock.mockReturnValue({
      data: ref(null),
      error: ref(new Error('connection refused')),
    })

    const wrapper = mountApp()

    expect(wrapper.get('[data-testid="backend-status"]').text()).toContain(
      '接続失敗',
    )
  })
})
