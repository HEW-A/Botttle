<template>
  <!-- 読み込み中 -->
  <div v-if="status === 'pending' && cards.length === 0" class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
    <div v-for="n in skeletonCount" :key="n" class="animate-pulse border border-gray-200">
      <div class="aspect-[4/3] bg-gray-100" />
      <div class="flex flex-col gap-2 p-3.5">
        <div class="h-5 w-20 bg-gray-100" />
        <div class="h-5 w-full bg-gray-100" />
        <div class="h-6 w-24 bg-gray-100" />
      </div>
    </div>
  </div>

  <!-- 取得失敗 -->
  <p v-else-if="error" class="border border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
    商品を読み込めませんでした。時間をおいて再度お試しください。
  </p>

  <!-- 0件 -->
  <p v-else-if="cards.length === 0" class="border border-gray-200 px-4 py-8 text-center text-sm text-gray-500">
    {{ emptyText }}
  </p>

  <div v-else class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
    <NuxtLink
      v-for="card in cards"
      :key="card.id"
      :to="`/chatbot/${card.id}`"
      class="block border border-gray-200 hover:border-blue-600"
    >
      <div class="flex aspect-[4/3] items-center justify-center overflow-hidden bg-gray-100 text-xs tracking-widest text-gray-400">
        <ProductThumbnail :src="card.thumbnailUrl" :alt="card.title">
          <span>NO IMAGE</span>
        </ProductThumbnail>
      </div>
      <div class="flex flex-col gap-2 p-3.5">
        <span v-if="card.tag" :class="categoryTagClass(card.categoryId)">{{ card.tag }}</span>
        <h4 class="text-base font-semibold">{{ card.title }}</h4>
        <span class="text-lg font-bold">{{ card.priceLabel }}</span>
      </div>
    </NuxtLink>
  </div>
</template>

<script setup lang="ts">
import type { Product } from '../../../types/product'

// 商品カードを4列で並べる。読み込み中・取得失敗・0件の表示もここで持つ
const props = withDefaults(
  defineProps<{
    products: Product[] | null | undefined
    /** useFetch の status */
    status: string
    error?: unknown
    emptyText?: string
    skeletonCount?: number
  }>(),
  {
    error: null,
    emptyText: 'まだ出品がありません。',
    skeletonCount: 4,
  },
)

const cards = computed(() => (props.products ?? []).map(toProductCard))
</script>
