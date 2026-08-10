<template>
  <div class="max-w-sm mx-auto py-20 px-4">
    <h2 class="text-xl font-bold mb-6 text-center">ログイン</h2>

    <form class="space-y-4" @submit.prevent="handleLogin">
      <div>
        <label class="block text-sm text-gray-600 mb-1">メールアドレス</label>
        <input
          v-model="email"
          type="email"
          required
          class="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label class="block text-sm text-gray-600 mb-1">パスワード</label>
        <input
          v-model="password"
          type="password"
          required
          class="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <p v-if="errorMessage" class="text-red-500 text-sm">{{ errorMessage }}</p>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-blue-600 text-white py-2 rounded-md font-medium hover:bg-blue-700 disabled:opacity-50"
      >
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>
    </form>
  </div>
</template>

<script setup>
const email = ref('')
const password = ref('')
const loading = ref(false)
const errorMessage = ref('')
const router = useRouter()

async function handleLogin() {
  loading.value = true
  errorMessage.value = ''

  // Supabase連携前の仮ロジック
  // 実際は const { error } = await supabase.auth.signInWithPassword({ email, password })
  setTimeout(() => {
    loading.value = false
    router.push('/main')
  }, 800)
}
</script>