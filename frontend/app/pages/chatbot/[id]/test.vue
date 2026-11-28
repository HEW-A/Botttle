<template>
  <CommonPageContainer size="narrow">
    <CommonPageHeader
      title="チャットボットをテスト"
      :description="`ここは作成したチャットボット（ID: ${chatbotId}）の動作テストページです。`"
    />
  </CommonPageContainer>
</template>

<script setup>
definePageMeta({
  middleware: 'auth',
})

useHead({
  title: 'チャットボットをテスト | botttle',
})

const route = useRoute()
const chatbotId = computed(() => route.params.id)
</script>
