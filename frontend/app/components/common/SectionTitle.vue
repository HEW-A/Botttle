<!-- カード・セクションの見出し（h2）。見出しレベルを変えたいときは as で指定する -->
<script setup lang="ts">
withDefaults(defineProps<{ as?: 'h2' | 'h3' }>(), {
  as: 'h2',
})
</script>

<template>
  <component :is="as" class="text-lg font-bold text-slate-900">
    <slot />
  </component>
</template>
