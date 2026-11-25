import type { Product, ProductCard } from '../../types/product'

export const CURRENCY_UNIT = 'BC'

/** 価格を「12,000 BC」の形に整形する。未設定(null)なら「価格未設定」 */
export function formatPrice(price: number | null | undefined): string {
  if (price === null || price === undefined) return '価格未設定'
  return `${price.toLocaleString('ja-JP')} ${CURRENCY_UNIT}`
}

/** 商品APIの1件を、ホーム画面の商品カードに表示する値に変換する */
export function toProductCard(product: Product): ProductCard {
  return {
    id: product.chatbot_id,
    title: product.bot_name,
    tag: product.category_name,
    categoryId: product.category_id,
    priceLabel: formatPrice(product.price),
    thumbnailUrl: product.thumbnail_url,
  }
}
