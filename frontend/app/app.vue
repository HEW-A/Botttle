<script setup lang="ts">
// backend との疎通確認: GET /api/health を呼び出して status を表示する
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { data, error } = useFetch<{ status: string }>(`${apiBase}/api/health`)
</script>

<template>
  <div class="min-h-screen bg-slate-50 p-6">
    <NuxtRouteAnnouncer />
    <p
      v-if="error"
      data-testid="backend-status"
      class="rounded-md bg-red-100 px-4 py-2 font-bold text-red-700"
    >
      接続失敗
    </p>
    <p
      v-else
      data-testid="backend-status"
      class="rounded-md bg-blue-100 px-4 py-2 font-bold text-blue-700"
    >
      Backend status: {{ data?.status }}
    </p>
    <NuxtPage />
  </div>
</template>
