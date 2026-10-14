<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <main class="flex-1">
      <div class="mx-auto flex w-full max-w-[640px] flex-col gap-1.5 px-6 py-14">
        <h1 class="text-2xl font-bold text-slate-900">チャットボットをテスト</h1>
        <p class="text-sm leading-relaxed text-slate-500">ここは作成したチャットボット（ID: {{ chatbotId }}）の動作テストページです。</p>
      </div>
    </main>

    <CommonAppFooter />
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
  middleware: 'auth',
})

useHead({
  title: 'チャットボットをテスト | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

const route = useRoute()
const chatbotId = computed(() => route.params.id)
</script>
