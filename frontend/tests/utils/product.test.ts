import { describe, expect, it } from 'vitest'
import type { Product } from '../../types/product'
import { formatPrice, toProductCard } from '../../app/utils/product'

const baseProduct: Product = {
  chatbot_id: '00000000-0000-0000-0000-000000000001',
  bot_name: '対応品質評価AI「サポたん」',
  price: 48000,
  description: '説明文',
  thumbnail_url: 'https://example.com/thumb.png',
  category_id: 1,
  username: 'sapo_lab',
  category_name: 'カスタマーサポート型',
}

describe('formatPrice', () => {
  it('3桁区切りとBCを付ける', () => {
    expect(formatPrice(48000)).toBe('48,000 BC')
    expect(formatPrice(1234567)).toBe('1,234,567 BC')
  })

  it('0円は 0 BC', () => {
    expect(formatPrice(0)).toBe('0 BC')
  })

  it('未設定(null/undefined)は「価格未設定」', () => {
    expect(formatPrice(null)).toBe('価格未設定')
    expect(formatPrice(undefined)).toBe('価格未設定')
  })
})

describe('toProductCard', () => {
  it('APIの項目をカードの表示項目に変換する', () => {
    expect(toProductCard(baseProduct)).toEqual({
      id: '00000000-0000-0000-0000-000000000001',
      title: '対応品質評価AI「サポたん」',
      tag: 'カスタマーサポート型',
      priceLabel: '48,000 BC',
      thumbnailUrl: 'https://example.com/thumb.png',
    })
  })

  it('カテゴリ・価格・サムネイルが未設定でも変換できる', () => {
    const card = toProductCard({ ...baseProduct, category_id: null, category_name: null, price: null, thumbnail_url: null })
    expect(card.tag).toBeNull()
    expect(card.priceLabel).toBe('価格未設定')
    expect(card.thumbnailUrl).toBeNull()
  })
})
