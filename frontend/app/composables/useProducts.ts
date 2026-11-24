import type { MaybeRefOrGetter } from 'vue'
import type { Category, Product } from '../../types/product'

// 商品API・カテゴリAPIの呼び出しをまとめた composable
// useFetch を使うので、SSR で取得したデータがそのままクライアントに引き継がれる

function apiBase() {
  return useRuntimeConfig().public.apiBase
}

export interface ProductListParams {
  limit?: number
  offset?: number
  categoryId?: number
}

/** 出品中の商品一覧(新しい順)。GET /api/products */
export function useProductList(params: MaybeRefOrGetter<ProductListParams> = {}) {
  const query = computed(() => {
    const { limit, offset, categoryId } = toValue(params)
    return { limit, offset, category_id: categoryId }
  })

  return useFetch<Product[]>('/api/products', {
    baseURL: apiBase(),
    query,
    default: () => [],
  })
}

/** 商品1件。GET /api/products/<chatbot_id>(見つからない場合は error.statusCode が 404) */
export function useProduct(chatbotId: MaybeRefOrGetter<string>) {
  return useFetch<Product>(() => `/api/products/${encodeURIComponent(toValue(chatbotId))}`, {
    baseURL: apiBase(),
  })
}

/** カテゴリ一覧(商品数つき)。GET /api/categories */
export function useCategories() {
  return useFetch<Category[]>('/api/categories', {
    baseURL: apiBase(),
    default: () => [],
  })
}
