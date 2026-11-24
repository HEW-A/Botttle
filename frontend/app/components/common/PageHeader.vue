<!-- ページの見出し（h1 + 説明文）。右側に置くボタンなどは #actions スロットへ -->
<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
    <div class="flex flex-col gap-1.5">
      <h1 class="text-2xl font-bold text-slate-900">{{ title }}</h1>
      <p v-if="description" class="text-sm text-slate-500">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex flex-none items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
