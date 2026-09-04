<script setup lang="ts">
// backend との疎通確認: GET /api/health を呼び出して status を表示する
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { data, error } = useFetch<{ status: string }>(`${apiBase}/api/health`)
</script>

<template>
  <header class="bg-white shadow-sm px-6 py-4 flex justify-between items-center">
    <NuxtLink to="/" class="font-bold text-lg text-blue-600">botttle</NuxtLink>
    <nav class="flex items-center space-x-4 text-sm">
      <p
        v-if="error"
        data-testid="backend-status"
        class="rounded-md bg-red-100 px-3 py-1 text-xs font-bold text-red-700"
      >
        接続失敗
      </p>
      <p
        v-else
        data-testid="backend-status"
        class="rounded-md bg-blue-100 px-3 py-1 text-xs font-bold text-blue-700"
      >
        Backend status: {{ data?.status }}
      </p>
      <NuxtLink to="/login" class="text-gray-600 hover:text-blue-600">ログイン</NuxtLink>
    </nav>
  </header>
</template>
