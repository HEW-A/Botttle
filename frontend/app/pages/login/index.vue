<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-10 font-['M_PLUS_1_Code']">
    <div class="w-full max-w-[400px] bg-white px-6 pt-6 pb-9 shadow-[0_20px_50px_-20px_rgba(15,23,42,0.25)] sm:px-10">
      <div class="mb-8 flex border-b border-slate-200">
        <button
          type="button"
          class="flex-1 border-b-2 py-3 text-sm font-semibold tracking-wide"
          :class="mode === 'signup' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-400'"
          @click="mode = 'signup'"
        >
          新規会員登録
        </button>
        <button
          type="button"
          class="flex-1 border-b-2 py-3 text-sm font-semibold tracking-wide"
          :class="mode === 'login' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-400'"
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
          <h2 class="mb-1.5 text-lg font-bold text-slate-900">おかえりなさい</h2>
          <p class="mb-6 text-xs text-slate-500">アカウントにログインしてください。</p>

          <label class="mb-1 block text-xs font-semibold text-slate-700">ユーザーID</label>
          <input
            v-model="loginUserId"
            type="text"
            required
            placeholder="user_id"
            class="mb-4 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <label class="mb-1 block text-xs font-semibold text-slate-700">パスワード</label>
          <input
            v-model="loginPassword"
            type="password"
            required
            placeholder="••••••••"
            class="mb-2.5 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <div class="mb-5 flex justify-end">
            <a href="#" class="text-xs text-blue-600 hover:text-blue-700">パスワードをお忘れですか？</a>
          </div>

          <p v-if="loginError" class="mb-3 text-sm text-red-500">{{ loginError }}</p>

          <button
            type="submit"
            :disabled="loginLoading"
            class="w-full bg-blue-600 py-3 text-sm font-semibold tracking-wide text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {{ loginLoading ? 'ログイン中...' : 'ログイン' }}
          </button>

          <p class="mt-5 text-center text-xs text-slate-500">
            アカウントをお持ちでないですか？
            <a href="#" class="font-semibold hover:text-blue-700" @click.prevent="mode = 'signup'">新規会員登録</a>
          </p>
        </form>

        <form
          class="col-start-1 row-start-1 max-w-[320px]"
          :class="mode === 'signup' ? '' : 'invisible'"
          :inert="mode !== 'signup'"
          @submit.prevent="handleSignup"
        >
          <h2 class="mb-1.5 text-lg font-bold text-slate-900">アカウントを作成</h2>
          <p class="mb-6 text-xs text-slate-500">1分で登録が完了します。</p>

          <label class="mb-1 block text-xs font-semibold text-slate-700">
            ユーザーID <span class="text-blue-600">*</span>
          </label>
          <input
            v-model="signupUserId"
            type="text"
            required
            placeholder="user_id"
            class="mb-3 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <label class="mb-1 block text-xs font-semibold text-slate-700">
            ユーザーネーム <span class="text-blue-600">*</span>
          </label>
          <input
            v-model="signupUsername"
            type="text"
            required
            placeholder="表示名"
            class="mb-3 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <label class="mb-1 block text-xs font-semibold text-slate-700">
            パスワード <span class="text-blue-600">*</span>
          </label>
          <input
            v-model="signupPassword"
            type="password"
            required
            placeholder="8文字以上"
            class="mb-3 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <label class="mb-1 block text-xs font-semibold text-slate-700">メールアドレス</label>
          <input
            v-model="signupEmail"
            type="email"
            placeholder="you@example.com"
            class="mb-5 w-full border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
          />

          <p v-if="signupError" class="mb-3 text-sm text-red-500">{{ signupError }}</p>

          <button
            type="submit"
            :disabled="signupLoading"
            class="w-full bg-blue-600 py-3 text-sm font-semibold tracking-wide text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {{ signupLoading ? '登録中...' : '登録する' }}
          </button>

          <p class="mt-5 text-center text-xs text-slate-500">
            すでにアカウントをお持ちですか？
            <a href="#" class="font-semibold hover:text-blue-700" @click.prevent="mode = 'login'">ログイン</a>
          </p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

useHead({
  title: 'ログイン / 新規会員登録 | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
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

async function handleLogin() {
  loginLoading.value = true
  loginError.value = ''

  // Supabase連携前の仮ロジック
  // 実際は const { error } = await supabase.auth.signInWithPassword({ email, password })
  setTimeout(() => {
    loginLoading.value = false
    router.push('/main')
  }, 800)
}

async function handleSignup() {
  signupLoading.value = true
  signupError.value = ''

  // Supabase連携前の仮ロジック
  // 実際は const { error } = await supabase.auth.signUp({ email, password })
  setTimeout(() => {
    signupLoading.value = false
    router.push('/main')
  }, 800)
}
</script>
