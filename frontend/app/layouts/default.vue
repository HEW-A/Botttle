<script setup lang="ts">
// backend との疎通確認: GET /api/health を呼び出して status を表示する
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { data, error } = useFetch<{ status: string }>(`${apiBase}/api/health`)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <CommonAppHeader />

    <p
      v-if="error"
      data-testid="backend-status"
      class="bg-red-50 px-4 py-1 text-center text-xs font-bold text-red-700"
    >
      接続失敗
    </p>
    <p
      v-else
      data-testid="backend-status"
      class="bg-blue-50 px-4 py-1 text-center text-xs font-bold text-blue-700"
    >
      Backend status: {{ data?.status }}
    </p>

    <main class="flex-1">
      <slot />
    </main>

    <CommonAppFooter />
  </div>
</template>
