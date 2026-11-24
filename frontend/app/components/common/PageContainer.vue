<!--
  ページ本文の幅と余白をそろえる入れ物。
  size="default" … 一覧・詳細など（ヘッダーと同じ max-w-7xl）
  size="narrow"  … 作成・出品などのフォーム画面
-->
<script setup lang="ts">
const props = withDefaults(defineProps<{ size?: 'default' | 'narrow' }>(), {
  size: 'default',
})

const widthClass = computed(() => (props.size === 'narrow' ? 'max-w-2xl' : 'max-w-7xl'))
</script>

<template>
  <div class="mx-auto w-full px-4 py-8 md:px-6" :class="widthClass">
    <slot />
  </div>
</template>
