// バックエンドの商品API・カテゴリAPIが返すJSONの型
// (backend/products/routes.py の _to_product、backend/categories/routes.py に対応)

/** GET /api/products, GET /api/products/<chatbot_id> の1件分 */
export interface Product {
  chatbot_id: string
  bot_name: string
  /** サイト内通貨(BC)での価格。DBでは未設定(null)もありうる */
  price: number | null
  description: string | null
  thumbnail_url: string | null
  category_id: number | null
  /** 出品者のユーザー名 */
  username: string | null
  category_name: string | null
}

/** GET /api/categories の1件分 */
export interface Category {
  category_id: number
  category_name: string
  /** 出品中(出品者が退会していない)の商品数 */
  product_count: number
}

/** 商品カード(ホーム画面の一覧)に表示する値 */
export interface ProductCard {
  id: string
  title: string
  /** カテゴリ名。未設定なら null(タグを表示しない) */
  tag: string | null
  /** 表示用に整形した価格(例: "12,000 BC") */
  priceLabel: string
  thumbnailUrl: string | null
}
