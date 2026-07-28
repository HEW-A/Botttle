<script setup lang="ts">
// nuxt.config.ts と .env の公開設定から、Flask APIの基本URLを読み込む
const config = useRuntimeConfig()

// Flaskの /api/botttles にデータを要求し、成功時は botttles、失敗時は error に結果を入れる
const { data: botttles, error } = await useFetch(
  `${config.public.apiBase}/api/botttles`
)
</script>

<template>
  <div>
    <p>top page (placeholder)</p>

    <p v-if="error">
      データの取得に失敗しました: {{ error.message }}
    </p>

    <ul v-else-if="botttles">
      <li v-for="botttle in botttles" :key="botttle.id">
        {{ botttle }}
      </li>
    </ul>

    <p v-else>データを読み込み中です。</p>
  </div>
</template>
