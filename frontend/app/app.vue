<script setup lang="ts">
// backend との疎通確認: GET /api/health を呼び出して status を表示する
const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const { data, error } = useFetch<{ status: string }>(`${apiBase}/api/health`)
</script>

<template>
  <div>
    <NuxtRouteAnnouncer />
    <p v-if="error" data-testid="backend-status">接続失敗</p>
    <p v-else data-testid="backend-status">Backend status: {{ data?.status }}</p>
    <NuxtPage />
  </div>
</template>
