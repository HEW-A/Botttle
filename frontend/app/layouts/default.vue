<script setup lang="ts">
// backend との疎通確認: GET /api/health を呼び出して status を表示する
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { data, error } = useFetch<{ status: string }>(`${apiBase}/api/health`)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <CommonAppHeader />

    <main class="flex-1">
      <slot />
    </main>

    <CommonAppFooter />
  </div>
</template>
