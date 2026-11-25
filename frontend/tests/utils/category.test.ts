import { describe, expect, it } from 'vitest'
import { DEFAULT_CATEGORY_ICON, categoryIcon, categoryTagClass } from '../../app/utils/category'

describe('categoryIcon', () => {
  it('1〜6 はそれぞれ専用のアイコンを返す', () => {
    const icons = [1, 2, 3, 4, 5, 6].map((id) => categoryIcon(id))
    for (const icon of icons) {
      expect(icon).not.toBe(DEFAULT_CATEGORY_ICON)
    }
    // 6つとも別のアイコン
    expect(new Set(icons).size).toBe(6)
  })

  it('対応の無いIDや未設定は共通のアイコンを返す', () => {
    expect(categoryIcon(7)).toBe(DEFAULT_CATEGORY_ICON)
    expect(categoryIcon(0)).toBe(DEFAULT_CATEGORY_ICON)
    expect(categoryIcon(null)).toBe(DEFAULT_CATEGORY_ICON)
    expect(categoryIcon(undefined)).toBe(DEFAULT_CATEGORY_ICON)
  })
})

describe('categoryTagClass', () => {
  it('カテゴリIDの順に3色を繰り返す', () => {
    expect(categoryTagClass(1)).toContain('bg-blue-100')
    expect(categoryTagClass(2)).toContain('bg-slate-100')
    expect(categoryTagClass(3)).toContain('border-blue-600')
    expect(categoryTagClass(4)).toBe(categoryTagClass(1))
    expect(categoryTagClass(7)).toBe(categoryTagClass(1))
  })

  it('未設定や不正なIDはグレーのタグにする', () => {
    expect(categoryTagClass(null)).toContain('bg-slate-100')
    expect(categoryTagClass(undefined)).toContain('bg-slate-100')
    expect(categoryTagClass(0)).toContain('bg-slate-100')
  })

  it('どの色にも共通の形のクラスが付く', () => {
    expect(categoryTagClass(1)).toContain('inline-flex')
    expect(categoryTagClass(null)).toContain('text-[11px]')
  })
})
