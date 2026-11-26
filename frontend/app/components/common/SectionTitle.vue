<!--
  セクションの見出し（h2）。
  size="md" … カード・パネルの中の見出し（既定）
  size="lg" … カードを使わずページに直接並べるセクションの見出し（メインページなど）
  見出しレベルを変えたいときは as で指定する
-->
<script setup lang="ts">
withDefaults(
  defineProps<{
    as?: 'h2' | 'h3'
    size?: 'md' | 'lg'
  }>(),
  {
    as: 'h2',
    size: 'md',
  },
)
</script>

<template>
  <component :is="as" class="font-bold text-slate-900" :class="size === 'lg' ? 'text-2xl' : 'text-lg'">
    <slot />
  </component>
</template>
