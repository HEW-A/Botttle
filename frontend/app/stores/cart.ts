export interface CartItem {
  id: string
  name: string
  seller: string
  price: number
  tags: string[]
}

// カートに入れたチャットボットを保持するstore
// チャットボットは利用権の購入のため、同じ商品は1点までとする(数量の概念を持たない)
// カートAPIが未実装のため、メモリ上でのみ保持する(バックエンド連携時に置き換え予定)
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const count = computed(() => items.value.length)
  const subtotal = computed(() => items.value.reduce((sum, item) => sum + item.price, 0))

  function has(id: string) {
    return items.value.some((item) => item.id === id)
  }

  function add(item: CartItem) {
    if (has(item.id)) return
    items.value.push(item)
  }

  function remove(id: string) {
    items.value = items.value.filter((item) => item.id !== id)
  }

  function clear() {
    items.value = []
  }

  return { items, count, subtotal, has, add, remove, clear }
})
