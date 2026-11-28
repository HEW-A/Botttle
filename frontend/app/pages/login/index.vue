<template>
  <UCard class="w-full max-w-[400px]" :ui="{ body: 'px-6 pt-6 pb-9 sm:px-10 sm:pt-6 sm:pb-9' }">
    <div class="mb-8 flex border-b border-slate-200">
      <button
        type="button"
        class="flex-1 border-b-2 py-3 text-sm font-bold tracking-wide transition-colors"
        :class="mode === 'signup' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="mode = 'signup'"
      >
        新規会員登録
      </button>
      <button
        type="button"
        class="flex-1 border-b-2 py-3 text-sm font-bold tracking-wide transition-colors"
        :class="mode === 'login' ? 'border-primary text-primary' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="mode = 'login'"
      >
        ログイン
      </button>
    </div>

    <div class="grid">
      <form
        class="col-start-1 row-start-1 max-w-[320px]"
        :class="mode === 'login' ? '' : 'invisible'"
        :inert="mode !== 'login'"
        @submit.prevent="handleLogin"
      >
        <CommonSectionTitle class="mb-1.5">おかえりなさい</CommonSectionTitle>
        <p class="mb-6 text-xs text-slate-500">アカウントにログインしてください。</p>

        <label for="login-user-id" class="mb-1 block text-xs font-bold text-slate-700">ユーザーID</label>
        <UInput id="login-user-id" v-model="loginUserId" autocomplete="username" class="mb-4 w-full" type="text" required placeholder="user_id" />

        <label for="login-password" class="mb-1 block text-xs font-bold text-slate-700">パスワード</label>
        <UInput id="login-password" v-model="loginPassword" autocomplete="current-password" class="mb-2.5 w-full" type="password" required placeholder="••••••••" />

        <div class="mb-5 flex justify-end">
          <a href="#" class="text-xs text-primary hover:underline">パスワードをお忘れですか？</a>
        </div>

        <p v-if="loginError" class="mb-3 text-sm text-red-600">{{ loginError }}</p>

        <UButton type="submit" block size="lg" :disabled="loginLoading">
          {{ loginLoading ? 'ログイン中...' : 'ログイン' }}
        </UButton>

        <p class="mt-5 text-center text-xs text-slate-500">
          アカウントをお持ちでないですか？
          <a href="#" class="font-bold text-primary hover:underline" @click.prevent="mode = 'signup'">新規会員登録</a>
        </p>
      </form>

      <form
        class="col-start-1 row-start-1 max-w-[320px]"
        :class="mode === 'signup' ? '' : 'invisible'"
        :inert="mode !== 'signup'"
        @submit.prevent="handleSignup"
      >
        <CommonSectionTitle class="mb-1.5">アカウントを作成</CommonSectionTitle>
        <p class="mb-6 text-xs text-slate-500">1分で登録が完了します。</p>

        <label for="signup-user-id" class="mb-1 block text-xs font-bold text-slate-700">
          ユーザーID <span class="text-primary">*</span>
        </label>
        <UInput id="signup-user-id" v-model="signupUserId" autocomplete="username" class="mb-3 w-full" type="text" required placeholder="user_id" />

        <label for="signup-username" class="mb-1 block text-xs font-bold text-slate-700">
          ユーザーネーム <span class="text-primary">*</span>
        </label>
        <UInput id="signup-username" v-model="signupUsername" autocomplete="nickname" class="mb-3 w-full" type="text" required placeholder="表示名" />

        <label for="signup-password" class="mb-1 block text-xs font-bold text-slate-700">
          パスワード <span class="text-primary">*</span>
        </label>
        <UInput
          id="signup-password"
          v-model="signupPassword"
          autocomplete="new-password"
          class="mb-3 w-full"
          type="password"
          required
          minlength="8"
          placeholder="8文字以上"
        />

        <label for="signup-email" class="mb-1 block text-xs font-bold text-slate-700">メールアドレス</label>
        <UInput id="signup-email" v-model="signupEmail" autocomplete="email" class="mb-5 w-full" type="email" placeholder="you@example.com" />

        <p v-if="signupError" class="mb-3 text-sm text-red-600">{{ signupError }}</p>

        <UButton type="submit" block size="lg" :disabled="signupLoading">
          {{ signupLoading ? '登録中...' : '登録する' }}
        </UButton>

        <p class="mt-5 text-center text-xs text-slate-500">
          すでにアカウントをお持ちですか？
          <a href="#" class="font-bold text-primary hover:underline" @click.prevent="mode = 'login'">ログイン</a>
        </p>
      </form>
    </div>
  </UCard>
</template>

<script setup>
definePageMeta({
  layout: 'auth',
  middleware: 'guest',
})

useHead({
  title: 'ログイン / 新規会員登録 | botttle',
})

const route = useRoute()
const router = useRouter()

const mode = ref(route.query.tab === 'register' ? 'signup' : 'login')

// タブ切り替えをURLの?tabに反映し、直リンク/共有時も同じタブを開けるようにする
watch(mode, (newMode) => {
  const tab = newMode === 'signup' ? 'register' : 'login'
  if (route.query.tab !== tab) {
    router.replace({ query: { ...route.query, tab } })
  }
})

watch(
  () => route.query.tab,
  (tab) => {
    const newMode = tab === 'register' ? 'signup' : 'login'
    if (mode.value !== newMode) {
      mode.value = newMode
    }
  },
)

const loginUserId = ref('')
const loginPassword = ref('')
const loginLoading = ref(false)
const loginError = ref('')

const signupUserId = ref('')
const signupUsername = ref('')
const signupPassword = ref('')
const signupEmail = ref('')
const signupLoading = ref(false)
const signupError = ref('')

const authStore = useAuthStore()

async function handleLogin() {
  loginLoading.value = true
  loginError.value = ''

  try {
    await authStore.login(loginUserId.value, loginPassword.value)
    router.push('/main')
  } catch (e) {
    loginError.value = e?.data?.error ?? 'ログインに失敗しました'
  } finally {
    loginLoading.value = false
  }
}

async function handleSignup() {
  signupLoading.value = true
  signupError.value = ''

  try {
    await authStore.signup(signupUserId.value, signupUsername.value, signupPassword.value, signupEmail.value)
    router.push('/main')
  } catch (e) {
    signupError.value = e?.data?.error ?? '登録に失敗しました'
  } finally {
    signupLoading.value = false
  }
}
</script>
