<!--
  ページ本文の幅と余白をそろえる入れ物。
  size="default" … 一覧・詳細など（max-w-6xl）
  size="wide"    … 3 列などで横幅を広く使う画面（max-w-7xl。ヘッダーと同じ幅）
  size="narrow"  … 作成・出品などのフォーム画面
  padded=false   … 上下の余白を付けない（セクションごとに上下の余白を持つページ用）
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    size?: 'default' | 'wide' | 'narrow'
    padded?: boolean
  }>(),
  {
    size: 'default',
    padded: true,
  },
)

const WIDTH_CLASSES = {
  default: 'max-w-6xl',
  wide: 'max-w-7xl',
  narrow: 'max-w-2xl',
} as const

const widthClass = computed(() => WIDTH_CLASSES[props.size])
</script>

<template>
  <div class="mx-auto w-full px-4 md:px-8" :class="[widthClass, { 'py-10': padded }]">
    <slot />
  </div>
</template>
