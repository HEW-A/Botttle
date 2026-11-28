<template>
  <div>
    <!-- 手順の表示(横幅いっぱいの帯にするため、PageContainer の外に置く) -->
    <div class="border-b border-slate-200 bg-white">
      <CommonPageContainer :padded="false" class="flex items-center gap-2 py-3 text-sm text-slate-500">
        <span :class="{ 'font-bold text-primary': !confirmed }">カート・お支払い</span>
        <span aria-hidden="true">→</span>
        <span :class="{ 'font-bold text-primary': confirmed }">完了</span>
      </CommonPageContainer>
    </div>

    <CommonPageContainer v-if="!confirmed">
      <CommonPageHeader title="カート" description="ご注文内容をご確認のうえ、サイト内通貨（BC）でお支払いを確定してください。" />

      <UCard v-if="cartStore.count === 0" :ui="{ body: 'flex flex-col items-center gap-4 p-10 text-center sm:p-10' }">
        <p class="text-sm text-slate-700">カートに商品が入っていません。</p>
        <UButton to="/main">チャットボットを探す</UButton>
      </UCard>

      <div v-else class="grid grid-cols-1 items-start gap-6 lg:grid-cols-[1fr_380px]">
        <!-- left column -->
        <div class="flex flex-col gap-6">
          <UCard as="section">
            <CommonSectionTitle class="mb-3">ご注文商品（{{ cartStore.count }}点）</CommonSectionTitle>
            <div class="flex flex-col">
              <div
                v-for="(item, index) in cartStore.items"
                :key="item.id"
                class="flex items-center gap-4 py-4"
                :class="{ 'border-t border-slate-200': index > 0 }"
              >
                <div class="flex size-19 flex-none items-center justify-center border border-slate-200 bg-slate-50 text-slate-400">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <rect x="3" y="4" width="18" height="16" rx="2"></rect>
                    <path d="M8 9h8"></path>
                    <path d="M8 13h5"></path>
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <NuxtLink :to="`/chatbot/${item.id}`" class="text-base font-bold text-slate-900 hover:text-primary">{{ item.name }}</NuxtLink>
                  <div class="my-1 text-xs text-slate-500">出品者: {{ item.seller }}</div>
                  <div class="flex flex-wrap gap-1.5">
                    <span v-for="tag in item.tags" :key="tag" class="bg-primary-100 px-2.5 py-1 text-xs font-bold text-primary-800">{{ tag }}</span>
                  </div>
                </div>
                <div class="flex flex-none flex-col items-end gap-1">
                  <div class="text-base font-bold text-slate-900">{{ formatNumber(item.price) }} BC</div>
                  <UButton color="error" variant="ghost" size="sm" @click="cartStore.remove(item.id)">削除</UButton>
                </div>
              </div>
            </div>
          </UCard>

          <UCard as="section">
            <CommonSectionTitle class="mb-3">お支払い方法</CommonSectionTitle>

            <label class="flex cursor-pointer items-center justify-between gap-3 border-b border-slate-200 py-3">
              <span class="flex items-center gap-2 text-sm text-slate-900">
                <input type="radio" name="pay" checked class="size-4 accent-primary" />
                保有BCで支払う
              </span>
              <span class="border border-primary px-2.5 py-1 text-xs font-bold text-primary">残高 {{ formatNumber(balance) }} BC</span>
            </label>
            <label class="flex cursor-not-allowed items-center justify-between gap-3 py-3 opacity-50">
              <span class="flex items-center gap-2 text-sm text-slate-900">
                <input type="radio" name="pay" disabled class="size-4 accent-primary" />
                クレジットカードでチャージして支払う
              </span>
              <span class="bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">準備中</span>
            </label>
          </UCard>

          <UCard as="section">
            <!-- UCheckbox はチェックマークのアイコンを外部(Iconify)から取得するため、ラジオと同じくブラウザ標準のものを使う -->
            <label class="flex cursor-pointer items-start gap-2.5 text-sm text-slate-700">
              <input v-model="agreed" type="checkbox" class="mt-0.5 size-4 flex-none accent-primary" />
              <span>「<a href="#" class="text-primary hover:underline">利用規約</a>」および「<a href="#" class="text-primary hover:underline">チャットボット利用ガイドライン</a>」に同意のうえ購入します。</span>
            </label>
          </UCard>
        </div>

        <!-- right column -->
        <UCard class="lg:sticky lg:top-20" :ui="{ body: 'flex flex-col gap-3.5' }">
          <CommonSectionTitle>注文サマリー</CommonSectionTitle>

          <div class="flex items-baseline justify-between text-lg font-bold">
            <span class="text-slate-900">合計<span class="ml-1 text-sm font-normal text-slate-500">（{{ cartStore.count }}点）</span></span>
            <span class="text-primary">{{ formatNumber(total) }} BC</span>
          </div>

          <div class="h-px bg-slate-200"></div>
          <div class="flex flex-col gap-2 text-sm">
            <div class="flex items-baseline justify-between"><span class="text-slate-500">保有残高</span><span class="text-slate-900">{{ formatNumber(balance) }} BC</span></div>
            <div class="flex items-baseline justify-between">
              <span class="text-slate-500">支払い後残高</span>
              <span class="font-bold" :class="insufficient ? 'text-red-600' : 'text-slate-900'">{{ formatNumber(remaining) }} BC</span>
            </div>
          </div>

          <template v-if="insufficient">
            <div class="border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">
              残高が不足しています。チャージしてから購入を確定してください。
            </div>
            <UButton block variant="outline">BCをチャージする</UButton>
          </template>

          <UButton block size="lg" class="mt-1" :disabled="!canConfirm" @click="onConfirm">
            {{ formatNumber(total) }} BCを支払って購入を確定する
          </UButton>
          <UButton block variant="ghost" @click="router.back()">買い物を続ける</UButton>

          <p class="text-xs leading-relaxed text-slate-500">購入確定後、チャットボットの利用権はすぐに付与されます。BCはサイト内でのみご利用いただけます。</p>
        </UCard>
      </div>
    </CommonPageContainer>

    <CommonPageContainer v-else size="narrow" :padded="false" class="py-24">
      <UCard :ui="{ body: 'flex flex-col items-center gap-3.5 p-8 text-center sm:p-8' }">
        <div class="flex size-14 items-center justify-center rounded-full border-2 border-primary text-primary">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M20 6L9 17l-5-5"></path>
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-slate-900">お支払いが完了しました</h1>
        <p class="text-sm text-slate-500">注文番号 {{ order.number }}</p>
        <div class="h-px w-full bg-slate-200"></div>
        <div class="flex w-full items-baseline justify-between text-sm"><span class="text-slate-500">購入点数</span><span class="text-slate-900">{{ order.count }}点</span></div>
        <div class="flex w-full items-baseline justify-between text-sm"><span class="text-slate-500">お支払い金額</span><span class="font-bold text-slate-900">{{ formatNumber(order.total) }} BC</span></div>
        <div class="flex w-full items-baseline justify-between text-sm"><span class="text-slate-500">残りの保有残高</span><span class="text-slate-900">{{ formatNumber(balance) }} BC</span></div>
        <UButton block size="lg" class="mt-1.5" to="/chat">チャットボットを利用開始する</UButton>
        <UButton block variant="ghost" :to="`/users/${authStore.user?.user_id}/purchase-history`">購入履歴を見る</UButton>
      </UCard>
    </CommonPageContainer>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: 'auth',
})

const router = useRouter()
const cartStore = useCartStore()
const authStore = useAuthStore()

useHead({
  title: 'カート | botttle',
})

// 残高取得・決済APIが未実装のため、モック値で画面を成立させる(バックエンド連携時に置き換え予定)
const balance = ref(8500)
const agreed = ref(false)
const confirmed = ref(false)
// 購入確定時にカートを空にするため、完了画面の表示内容は確定時点の値を保持しておく
const order = ref({ number: '', count: 0, total: 0 })

const subtotal = computed(() => cartStore.subtotal)
// 手数料は取らないため、合計は小計と同じ
const total = computed(() => subtotal.value)
const remaining = computed(() => balance.value - total.value)
const insufficient = computed(() => remaining.value < 0)
const canConfirm = computed(() => cartStore.count > 0 && agreed.value && !insufficient.value)

function formatNumber(value) {
  return value.toLocaleString()
}

function onConfirm() {
  if (!canConfirm.value) return
  order.value = { number: `CB-${Date.now()}`, count: cartStore.count, total: total.value }
  balance.value = remaining.value
  cartStore.clear()
  confirmed.value = true
}
</script>
