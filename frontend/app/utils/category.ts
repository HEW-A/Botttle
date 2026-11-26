// カテゴリの見た目(アイコン・タグの色)はDBに持たないため、category_id から画面側で決める。
// ID は共有の Supabase のカテゴリ(1〜5)に合わせている。
// カテゴリを増やす・変える場合は、共有の Supabase とこの対応をそろえること。
// 対応の無いID(後から追加されたカテゴリなど)でも表示が崩れないよう、共通の見た目を返す。

// SVG の中身(<svg> の子要素)。v-html で埋め込むので、ここには固定の文字列だけを書くこと
const CATEGORY_ICONS: Record<number, string> = {
  // 仕事・キャリア型(カバン)
  1: '<rect x="2" y="7" width="20" height="14" rx="0"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>',
  // 予約・受付型(カレンダー)
  2: '<rect x="3" y="4" width="18" height="18" rx="0"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>',
  // 多言語対応型(地球)
  3: '<circle cx="12" cy="12" r="9"></circle><path d="M12 3a15 15 0 0 0 0 18M3 12h18"></path>',
  // カスタマーサポート型(吹き出し)
  4: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>',
  // 学習・教育型(本)
  5: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
}

// 対応の無いカテゴリ用(値札の形のアイコン)
export const DEFAULT_CATEGORY_ICON =
  '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line>'

/** カテゴリのアイコン(SVGの中身)を返す */
export function categoryIcon(categoryId: number | null | undefined): string {
  if (categoryId === null || categoryId === undefined) return DEFAULT_CATEGORY_ICON
  return CATEGORY_ICONS[categoryId] ?? DEFAULT_CATEGORY_ICON
}

const TAG_BASE_CLASS = 'inline-flex w-fit items-center px-2.5 py-1 text-xs'

// 商品カードのカテゴリタグの色。カテゴリIDの順に繰り返し割り当てる
const TAG_VARIANT_CLASSES = [
  'bg-blue-100 text-blue-800',
  'bg-slate-100 text-slate-800',
  'border border-blue-600 text-blue-600',
]

/** 商品カードのカテゴリタグのクラスを返す。同じカテゴリは常に同じ色になる */
export function categoryTagClass(categoryId: number | null | undefined): string {
  if (categoryId === null || categoryId === undefined || categoryId < 1) {
    return `${TAG_BASE_CLASS} ${TAG_VARIANT_CLASSES[1]}`
  }
  const variant = TAG_VARIANT_CLASSES[(categoryId - 1) % TAG_VARIANT_CLASSES.length]
  return `${TAG_BASE_CLASS} ${variant}`
}
