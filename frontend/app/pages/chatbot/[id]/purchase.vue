<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <div class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-5xl items-center gap-2 px-6 py-3 text-[13px] text-slate-500">
        <span>商品</span>
        <span class="opacity-50">→</span>
        <span class="font-bold text-blue-600">お支払い</span>
        <span class="opacity-50">→</span>
        <span>完了</span>
      </div>
    </div>

    <main class="flex-1">
      <div v-if="!confirmed" class="mx-auto max-w-5xl px-6 py-9">
        <div class="mb-7 flex flex-col gap-1.5">
          <h1 class="text-2xl font-bold text-slate-900">お支払い手続き</h1>
          <p class="text-sm text-slate-500">ご注文内容をご確認のうえ、サイト内通貨（SC）でお支払いを確定してください。</p>
        </div>

        <div class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_380px]">
          <!-- left column -->
          <div class="flex flex-col gap-6">
            <section class="border-2 border-slate-900 bg-white p-6">
              <h2 class="mb-3 text-lg font-bold text-slate-900">ご注文商品</h2>
              <div class="flex items-center gap-4">
                <div class="flex h-[76px] w-[76px] flex-none items-center justify-center border border-slate-200 bg-slate-50">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="4" width="18" height="16" rx="2"></rect>
                    <path d="M8 9h8"></path>
                    <path d="M8 13h5"></path>
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-[15px] font-bold text-slate-900">{{ item.name }}</div>
                  <div class="my-1 text-xs text-slate-500">出品者: {{ item.seller }}</div>
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="tag in item.tags" :key="tag" class="bg-blue-100 px-2.5 py-1 text-[11px] font-bold text-blue-800">{{ tag }}</span>
                  </div>
                </div>
                <div class="flex-none text-right">
                  <div class="text-xs text-slate-500">数量: 1</div>
                  <div class="mt-1 text-base font-bold text-slate-900">{{ formatNumber(item.price) }} SC</div>
                </div>
              </div>
            </section>

            <section class="border-2 border-slate-900 bg-white p-6">
              <h2 class="mb-3 text-lg font-bold text-slate-900">お支払い方法</h2>

              <label class="flex items-center justify-between gap-3 border-b border-slate-200 py-3 cursor-pointer">
                <span class="flex items-center gap-2 text-sm text-slate-900">
                  <input type="radio" name="pay" checked class="h-4 w-4 accent-blue-600" />
                  保有サイトコインで支払う
                </span>
                <span class="border border-blue-600 px-2.5 py-1 text-[11px] font-bold text-blue-600">残高 {{ formatNumber(balance) }} SC</span>
              </label>
              <label class="flex items-center justify-between gap-3 py-3 opacity-50 cursor-not-allowed">
                <span class="flex items-center gap-2 text-sm text-slate-900">
                  <input type="radio" name="pay" disabled class="h-4 w-4 accent-blue-600" />
                  クレジットカードでチャージして支払う
                </span>
                <span class="bg-slate-100 px-2.5 py-1 text-[11px] font-bold text-slate-700">準備中</span>
              </label>
            </section>

            <section class="border-2 border-slate-900 bg-white p-6">
              <label class="flex items-start gap-2.5 text-[13px] text-slate-700 cursor-pointer">
                <input v-model="agreed" type="checkbox" class="mt-0.5 h-4 w-4 flex-none accent-blue-600" />
                <span>「<a href="#" class="text-blue-600 hover:text-blue-700">利用規約</a>」および「<a href="#" class="text-blue-600 hover:text-blue-700">チャットボット利用ガイドライン</a>」に同意のうえ購入します。</span>
              </label>
            </section>
          </div>

          <!-- right column -->
          <div class="sticky top-20 flex flex-col gap-3.5 border-2 border-slate-900 bg-white p-6">
            <h2 class="text-lg font-bold text-slate-900">注文サマリー</h2>

            <div class="flex flex-col gap-2 text-sm">
              <div class="flex items-baseline justify-between"><span class="text-slate-500">小計</span><span class="text-slate-900">{{ formatNumber(subtotal) }} SC</span></div>
              <div class="flex items-baseline justify-between"><span class="text-slate-500">プラットフォーム手数料（{{ feeRatePercent }}%）</span><span class="text-slate-900">{{ formatNumber(fee) }} SC</span></div>
            </div>
            <div class="h-px bg-slate-200"></div>
            <div class="flex items-baseline justify-between text-lg font-bold"><span class="text-slate-900">合計</span><span class="text-blue-600">{{ formatNumber(total) }} SC</span></div>

            <div class="h-px bg-slate-200"></div>
            <div class="flex flex-col gap-2 text-sm">
              <div class="flex items-baseline justify-between"><span class="text-slate-500">保有残高</span><span class="text-slate-900">{{ formatNumber(balance) }} SC</span></div>
              <div class="flex items-baseline justify-between">
                <span class="text-slate-500">支払い後残高</span>
                <span class="font-bold" :class="insufficient ? 'text-red-600' : 'text-slate-900'">{{ formatNumber(remaining) }} SC</span>
              </div>
            </div>

            <template v-if="insufficient">
              <div class="border border-red-600 px-3 py-2 text-xs text-red-600">
                残高が不足しています。チャージしてから購入を確定してください。
              </div>
              <button type="button" class="w-full border-2 border-slate-700 bg-white py-3 text-sm font-bold text-slate-700">
                サイトコインをチャージする
              </button>
            </template>

            <button
              type="button"
              class="mt-1 w-full border-2 border-transparent py-3 text-[15px] font-bold"
              :class="canConfirm ? 'cursor-pointer bg-blue-600 text-white' : 'cursor-not-allowed bg-slate-200 text-slate-400'"
              :disabled="!canConfirm"
              @click="onConfirm"
            >
              {{ formatNumber(total) }} SCを支払って購入を確定する
            </button>
            <button type="button" class="w-full py-2 text-center text-sm font-bold text-slate-700" @click="router.back()">
              商品ページに戻る
            </button>

            <p class="text-[11px] leading-relaxed text-slate-500">購入確定後、チャットボットの利用権はすぐに付与されます。SC（サイトコイン）はサイト内でのみご利用いただけます。</p>
          </div>
        </div>
      </div>

      <div v-else class="mx-auto max-w-xl px-6 py-24">
        <div class="flex flex-col items-center gap-3.5 border-2 border-slate-900 bg-white p-8 text-center">
          <div class="flex h-14 w-14 items-center justify-center rounded-full border-2 border-blue-600">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 6L9 17l-5-5"></path>
            </svg>
          </div>
          <h2 class="text-xl font-bold text-slate-900">お支払いが完了しました</h2>
          <p class="text-sm text-slate-500">注文番号 {{ orderNumber }}</p>
          <div class="h-px w-full bg-slate-200"></div>
          <div class="flex w-full items-baseline justify-between text-sm"><span class="text-slate-500">お支払い金額</span><span class="font-bold text-slate-900">{{ formatNumber(total) }} SC</span></div>
          <div class="flex w-full items-baseline justify-between text-sm"><span class="text-slate-500">残りの保有残高</span><span class="text-slate-900">{{ formatNumber(remaining) }} SC</span></div>
          <NuxtLink to="/chat" class="mt-1.5 w-full border-2 border-blue-600 bg-blue-600 py-3 text-sm font-bold text-white">
            チャットボットを利用開始する
          </NuxtLink>
          <NuxtLink to="/mypage" class="w-full py-2 text-center text-sm font-bold text-slate-700">
            購入履歴を見る
          </NuxtLink>
        </div>
      </div>
    </main>

    <CommonAppFooter />
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

const route = useRoute()
const router = useRouter()

useHead({
  title: 'お支払い手続き | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

// チャットボット出品APIが購入向けの商品取得を提供していないため、
// id をキーにしたモックデータで画面を成立させる(バックエンド連携時に置き換え予定)
const mockItems = {
  1: { name: '接客対応AIチャットボット Pro', seller: 'botlab_yuki', price: 4800, tags: ['商用利用可', '即時ダウンロード'] },
  2: { name: 'FAQ自動応答ボット ライトプラン', seller: 'helpdesk_taro', price: 1200, tags: ['個人利用'] },
}
const item = computed(() => mockItems[route.params.id] ?? { name: `チャットボット #${route.params.id}`, seller: '出品者未設定', price: 3000, tags: ['個人利用'] })

const feeRatePercent = 5
const balance = ref(8500)
const agreed = ref(false)
const confirmed = ref(false)
const orderNumber = ref('')

const subtotal = computed(() => item.value.price)
const fee = computed(() => Math.round(subtotal.value * feeRatePercent / 100))
const total = computed(() => subtotal.value + fee.value)
const remaining = computed(() => balance.value - total.value)
const insufficient = computed(() => remaining.value < 0)
const canConfirm = computed(() => agreed.value && !insufficient.value)

function formatNumber(value) {
  return value.toLocaleString()
}

function onConfirm() {
  if (!canConfirm.value) return
  orderNumber.value = `CB-${Date.now()}`
  confirmed.value = true
}
</script>
