<!--
  ページ本文の幅と余白をそろえる入れ物。
  size="default" … 一覧・詳細など（max-w-6xl）
  size="narrow"  … 作成・出品などのフォーム画面
  padded=false   … 上下の余白を付けない（セクションごとに上下の余白を持つページ用）
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    size?: 'default' | 'narrow'
    padded?: boolean
  }>(),
  {
    size: 'default',
    padded: true,
  },
)

const widthClass = computed(() => (props.size === 'narrow' ? 'max-w-2xl' : 'max-w-6xl'))
</script>

<template>
  <div class="mx-auto w-full px-4 md:px-8" :class="[widthClass, { 'py-10': padded }]">
    <slot />
  </div>
</template>
