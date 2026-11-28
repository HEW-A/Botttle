<template>
  <CommonPageContainer>
    <!-- ============ モード選択 ============ -->
    <template v-if="step === 'mode'">
      <div class="mb-8 text-center">
        <h1 class="mb-2.5 text-2xl font-bold text-slate-900">対戦方法を選ぶ</h1>
        <p class="text-sm leading-relaxed text-slate-500">
          2体のボットに同じ質問を送り、良い回答をした方に投票します。
        </p>
      </div>
      <div class="mx-auto grid max-w-3xl grid-cols-1 gap-5 sm:grid-cols-2">
        <!-- カード全体が1つのボタン。中の「すぐに対戦する」等はボタン風の見た目だけ(ボタンの入れ子はできないため) -->
        <button
          type="button"
          class="flex cursor-pointer flex-col gap-3 border border-slate-200 bg-white p-7 text-left transition-colors hover:border-primary focus-visible:outline-2 focus-visible:outline-primary"
          @click="goRandom"
        >
          <span class="text-sm font-bold text-primary">匿名の2つを戦わせる</span>
          <span class="text-xl font-bold text-slate-900">{{ MODE_LABELS.random }}</span>
          <span class="text-sm leading-relaxed text-slate-500">
            出品中のボットから2体をランダムに選出。名前は投票後に公開されます。勝敗はランキングに影響します。
          </span>
          <span class="mt-2 inline-flex h-11 items-center self-start rounded-control bg-primary px-5 text-sm font-bold text-white">
            すぐに対戦する
          </span>
        </button>
        <button
          type="button"
          class="flex cursor-pointer flex-col gap-3 border border-slate-200 bg-white p-7 text-left transition-colors hover:border-primary focus-visible:outline-2 focus-visible:outline-primary"
          @click="goPick"
        >
          <span class="text-sm font-bold text-slate-700">指名した2つを戦わせる</span>
          <span class="text-xl font-bold text-slate-900">{{ MODE_LABELS.pick }}</span>
          <span class="text-sm leading-relaxed text-slate-500">
            検索・お気に入り・カテゴリからAとBのボットを自分で指定して比較します。この対戦はランキングに影響しません。
          </span>
          <span class="mt-2 inline-flex h-11 items-center self-start rounded-control bg-white px-5 text-sm font-bold text-primary ring ring-primary ring-inset">
            ボットを選ぶ
          </span>
        </button>
      </div>
    </template>

    <!-- ============ ボット選択 ============ -->
    <template v-else-if="step === 'pick'">
      <CommonPageHeader title="対戦するボットを選ぶ" description="AとBそれぞれに1体ずつ選択してください">
        <template #actions>
          <UButton variant="outline" @click="backToMode">戻る</UButton>
        </template>
      </CommonPageHeader>

      <div class="mb-7 grid grid-cols-1 gap-5 md:grid-cols-2">
        <UCard v-for="side in sideViews" :key="side.key" :ui="{ body: 'flex flex-col gap-3.5 p-5 sm:p-5' }">
          <div class="flex items-center justify-between gap-2.5">
            <div class="flex items-center gap-2.5">
              <div class="flex size-9 items-center justify-center rounded-full bg-primary-100 text-base font-bold text-primary-700" aria-hidden="true">
                {{ side.key }}
              </div>
              <CommonSectionTitle>ボット {{ side.key }}</CommonSectionTitle>
            </div>
            <span v-if="side.state.selected" class="max-w-44 truncate bg-primary-50 px-2.5 py-1 text-xs font-bold text-primary-700">
              {{ side.state.selected.name }}
            </span>
          </div>

          <UInput
            v-model="side.state.query"
            class="w-full"
            placeholder="ボット名・出品者で検索"
            :aria-label="`ボット ${side.key} を検索`"
          />

          <div class="grid grid-cols-2 gap-2.5">
            <UButton
              :variant="side.state.favOnly ? 'solid' : 'outline'"
              class="justify-center"
              :aria-pressed="side.state.favOnly"
              @click="side.state.favOnly = !side.state.favOnly"
            >
              お気に入りから選択
            </UButton>
            <UButton
              :variant="side.state.showCats || !!side.state.cat ? 'solid' : 'outline'"
              class="justify-center"
              :aria-pressed="side.state.showCats || !!side.state.cat"
              @click="toggleCats(side.state)"
            >
              カテゴリから検索
            </UButton>
          </div>

          <div v-if="side.state.showCats" class="flex flex-wrap gap-1.5">
            <UButton
              v-for="c in CATEGORIES"
              :key="c"
              size="sm"
              :variant="side.state.cat === c ? 'solid' : 'outline'"
              :aria-pressed="side.state.cat === c"
              @click="side.state.cat = side.state.cat === c ? null : c"
            >
              {{ c }}
            </UButton>
          </div>

          <div class="flex h-75 flex-col gap-1.5 overflow-y-auto pr-0.5">
            <button
              v-for="bot in side.results"
              :key="bot.id"
              type="button"
              :disabled="bot.taken"
              :aria-pressed="bot.selected"
              class="flex items-center gap-3 border px-3 py-2.5 text-left transition-colors hover:border-primary focus-visible:outline-2 focus-visible:outline-primary disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-200"
              :class="bot.selected ? 'border-primary bg-primary-50' : 'border-slate-200 bg-white'"
              @click="side.state.selected = bot.selected ? null : bot"
            >
              <div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700" aria-hidden="true">
                {{ bot.avatar }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm font-bold text-slate-900">{{ bot.name }}</div>
                <div class="text-xs text-slate-500">{{ bot.owner }} ・ {{ bot.category }}</div>
              </div>
              <span v-if="bot.fav" class="shrink-0 text-xs text-amber-500">
                <span aria-hidden="true">★</span>
                <span class="sr-only">お気に入り</span>
              </span>
            </button>
            <p v-if="!side.results.length" class="my-6 text-center text-sm text-slate-500">
              該当するボットがありません
            </p>
          </div>
        </UCard>
      </div>

      <div class="flex justify-center">
        <UButton size="lg" class="px-10" :disabled="!canStart" @click="startPicked">BCを100払って対戦</UButton>
      </div>
    </template>

    <!-- ============ アリーナ ============ -->
    <template v-else>
      <CommonPageHeader
        :title="`アリーナ ・ ${MODE_LABELS[mode]}`"
        :description="mode === 'random' ? 'ボットの正体は投票後に公開されます' : '同じ質問を両方のボットに送って比較しましょう'"
      >
        <template #actions>
          <UButton variant="outline" @click="backToMode">対戦をやめる</UButton>
        </template>
      </CommonPageHeader>

      <div class="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        <UCard
          v-for="pn in panels"
          :key="pn.key"
          as="section"
          class="flex h-105 flex-col"
          :ui="{
            header: 'flex items-center gap-2.5 px-4 py-3.5 sm:px-4',
            body: 'flex min-h-0 flex-1 flex-col p-0 sm:p-0',
          }"
        >
          <template #header>
            <div
              class="flex size-9 flex-none items-center justify-center rounded-full text-sm font-bold"
              :class="pn.anon ? 'bg-slate-200 text-slate-700' : 'bg-primary-100 text-primary-700'"
              aria-hidden="true"
            >
              {{ pn.avatar }}
            </div>
            <div class="min-w-0">
              <h2 class="text-sm font-bold text-slate-900">{{ pn.name }}</h2>
              <div class="text-xs text-slate-500">{{ pn.owner }}</div>
            </div>
          </template>

          <!-- 自分の質問(右)とボットの回答(左)を、A・B それぞれの欄に会話として並べる -->
          <CommonChatLog class="bg-slate-50 p-4" :aria-label="`${pn.name}との会話`">
            <template v-for="(msg, i) in pn.messages" :key="i">
              <CommonTypingIndicator v-if="msg.role === 'typing'" />
              <CommonChatBubble v-else :sender="msg.role">{{ msg.text }}</CommonChatBubble>
            </template>
          </CommonChatLog>
        </UCard>
      </div>

      <!-- form にして Enter で送信する(日本語の変換確定の Enter では送信されない) -->
      <form class="mb-5 flex gap-2.5" @submit.prevent="sendPrompt">
        <UInput
          v-model="input"
          class="min-w-0 flex-1"
          :disabled="sending"
          placeholder="両方のボットに送る質問を入力…"
          aria-label="両方のボットに送る質問"
        />
        <UButton type="submit" :disabled="sendDisabled">{{ sending ? '送信中…' : '送信' }}</UButton>
      </form>

      <p v-if="showVoteHint" class="mb-6 text-center text-xs text-slate-500">
        あと{{ exchangesLeft }}回のやり取りで投票が可能になります
      </p>

      <UCard v-if="showVotePanel" class="mb-5" :ui="{ body: 'p-5 sm:p-5' }">
        <CommonSectionTitle class="mb-3.5 text-center">どちらの回答が良かった？</CommonSectionTitle>
        <div class="flex flex-wrap justify-center gap-2.5">
          <UButton v-for="v in VOTE_DEFS" :key="v.key" variant="outline" @click="vote(v.key)">{{ v.label }}</UButton>
        </div>
      </UCard>

      <div v-if="voted" class="border border-primary-200 bg-primary-50 p-6 text-center">
        <p class="mb-1.5 text-sm font-bold text-primary-700">投票ありがとうございます</p>
        <p class="mb-4 text-sm text-slate-700">{{ resultText }}</p>
        <div class="flex flex-wrap justify-center gap-3">
          <UButton @click="rematch">もう一度対戦する</UButton>
          <UButton variant="outline" @click="backToMode">モード選択へ</UButton>
        </div>
      </div>
    </template>
  </CommonPageContainer>
</template>

<script setup>
// BotArena: 2体のボットに同じ質問を送って回答を比較し、投票するバトル機能。
// 対戦方法は「レート対戦(ランダム・匿名)」と「フリー対戦(指名)」の二択。レート対戦は投票後に正体を公開する。
// バックエンドAPIが未実装のため、本ページはダミーデータ・擬似応答によるフロントエンド単体のモックアップ。
// ヘッダー/フッターは共通レイアウト(layouts/default.vue)側が描画するため、ここでは持たない。

useHead({
  title: 'BotArena | botttle',
})

// 対戦モードの表示名。モード選択カードとアリーナ見出しで共通して使う
const MODE_LABELS = { random: 'レート対戦', pick: 'フリー対戦' }

// 対戦に必要なやり取り回数(これに達すると投票パネルが表示される)
const REQUIRED_EXCHANGES = 2

const BOTS = [
  { id: 'b1', name: 'レシピ相談員 ポタージュ', owner: '@yuki_cook', category: '料理', avatar: 'ポ', winRate: 68, fav: true },
  { id: 'b2', name: '旅程プランナー オデッセイ', owner: '@tabi_taro', category: '旅行', avatar: 'オ', winRate: 74, fav: true },
  { id: 'b3', name: '法律クイックQA リーガルビット', owner: '@legal_min', category: '法律', avatar: 'リ', winRate: 55, fav: false },
  { id: 'b4', name: '筋トレコーチ マッスルナビ', owner: '@fit_coach', category: 'フィットネス', avatar: 'マ', winRate: 81, fav: true },
  { id: 'b5', name: '家計簿アシスタント クレバー', owner: '@money_ken', category: '家計管理', avatar: 'ク', winRate: 62, fav: false },
  { id: 'b6', name: '英会話パートナー トーキー', owner: '@eng_mari', category: '語学', avatar: 'ト', winRate: 70, fav: true },
  { id: 'b7', name: '献立提案ロボ ククル', owner: '@kitchen_ai', category: '料理', avatar: 'コ', winRate: 58, fav: false },
  { id: 'b8', name: '韓国語チューター ハヌル', owner: '@hangul_s', category: '語学', avatar: 'ハ', winRate: 64, fav: false },
  { id: 'b9', name: '温泉ガイド ゆけむり', owner: '@onsen_lover', category: '旅行', avatar: 'ゆ', winRate: 59, fav: false },
  { id: 'b10', name: 'ストレッチ先生 ノビー', owner: '@yoga_rin', category: 'フィットネス', avatar: 'ノ', winRate: 66, fav: true },
]

const CATEGORIES = ['料理', '旅行', '法律', 'フィットネス', '家計管理', '語学']

const RESPONSES = {
  家計管理: ['固定費を先取りで管理すると、月末の変動費に余裕が生まれますよ。', 'まずは1週間だけレシートを記録して、支出の傾向を見てみましょう。'],
  語学: ['その表現は少しフォーマルすぎるかもしれません。カジュアルな場では別の言い回しがおすすめです。', '発音のコツは口をやや大きく開けることです。何度か声に出してみましょう。'],
  料理: ['旬の食材を使うと風味が引き立ちます。下味に塩と少量の酒を使うのがポイントです。', '火加減は中火をキープしつつ、途中で一度混ぜると失敗しにくいですよ。'],
  旅行: ['この時期は朝夕が冷えるので、薄手の羽織りがあると安心です。', '移動時間を短くするなら、拠点を1つに固めるプランがおすすめです。'],
  法律: ['一般的な見解としては、契約書に明記がない場合は民法の規定が適用されます。', '個別の事情によって結論が変わるため、専門家への相談も検討してください。'],
  フィットネス: ['まずはフォームを固めることが先です。回数より質を優先しましょう。', '週2回のペースから始めて、体の反応を見ながら調整していきましょう。'],
  default: ['なるほど、その内容について整理しますね。まず前提を確認すると…', 'ご質問ありがとうございます。ポイントは大きく2つあります。'],
}

function pickResponse(category, seed) {
  const list = RESPONSES[category] || RESPONSES.default
  return list[seed % list.length]
}

const VOTE_DEFS = [
  { key: 'A', label: 'Aが良い' },
  { key: 'B', label: 'Bが良い' },
  { key: 'tie', label: '引き分け' },
  { key: 'bad', label: 'どちらも微妙' },
]

const emptySide = () => ({ query: '', favOnly: false, showCats: false, cat: null, selected: null })

const step = ref('mode') // 'mode' | 'pick' | 'arena'
const mode = ref(null) // 'random' | 'pick'
const sideA = ref(emptySide())
const sideB = ref(emptySide())
const botA = ref(null)
const botB = ref(null)
const input = ref('')
const msgA = ref([])
const msgB = ref([])
const exchanges = ref(0)
const voted = ref(null) // null | 'A' | 'B' | 'tie' | 'bad'
const sending = ref(false)

// 擬似応答のタイマー。対戦を抜けた・再戦した・ページを離れたときに止め、
// 前の対戦の回答が新しい対戦に混ざらないようにする
const pendingTimers = []

function schedule(fn, ms) {
  const id = setTimeout(() => {
    pendingTimers.splice(pendingTimers.indexOf(id), 1)
    fn()
  }, ms)
  pendingTimers.push(id)
}

function clearPendingTimers() {
  pendingTimers.forEach(clearTimeout)
  pendingTimers.length = 0
}

onBeforeUnmount(clearPendingTimers)

// ---- ボット選択 ----
function filterBots(side, other) {
  const q = side.query.trim().toLowerCase()
  return BOTS.filter(
    (b) =>
      (!side.favOnly || b.fav) &&
      (!side.cat || b.category === side.cat) &&
      (!q || b.name.toLowerCase().includes(q) || b.owner.toLowerCase().includes(q)),
  ).map((b) => ({
    ...b,
    selected: side.selected?.id === b.id,
    // もう一方で選択済みのボットは選べない
    taken: other.selected?.id === b.id,
  }))
}

const sideViews = computed(() => [
  { key: 'A', state: sideA.value, results: filterBots(sideA.value, sideB.value) },
  { key: 'B', state: sideB.value, results: filterBots(sideB.value, sideA.value) },
])

const canStart = computed(() => !!(sideA.value.selected && sideB.value.selected))

function toggleCats(side) {
  if (side.showCats) {
    side.showCats = false
    side.cat = null
  } else {
    side.showCats = true
  }
}

// ---- 画面遷移 ----
function enterArena(nextMode, a, b) {
  clearPendingTimers()
  mode.value = nextMode
  botA.value = a
  botB.value = b
  input.value = ''
  msgA.value = []
  msgB.value = []
  exchanges.value = 0
  voted.value = null
  sending.value = false
  step.value = 'arena'
}

function goRandom() {
  const a = Math.floor(Math.random() * BOTS.length)
  let b = Math.floor(Math.random() * (BOTS.length - 1))
  if (b >= a) b++
  enterArena('random', BOTS[a], BOTS[b])
}

function goPick() {
  sideA.value = emptySide()
  sideB.value = emptySide()
  step.value = 'pick'
}

function backToMode() {
  clearPendingTimers()
  sending.value = false
  step.value = 'mode'
}

function startPicked() {
  if (canStart.value) enterArena('pick', sideA.value.selected, sideB.value.selected)
}

function rematch() {
  if (mode.value === 'random') goRandom()
  else enterArena('pick', botA.value, botB.value)
}

// ---- アリーナ ----
const panels = computed(() => {
  // レート対戦は投票まで匿名
  const anon = mode.value === 'random' && !voted.value
  const panel = (key, bot, messages) => ({
    key,
    anon,
    avatar: anon || !bot ? key : bot.avatar,
    name: anon || !bot ? `ボット ${key}` : bot.name,
    owner: anon || !bot ? '投票後に公開' : `${bot.owner} ・ ${bot.category}`,
    messages,
  })
  return [panel('A', botA.value, msgA.value), panel('B', botB.value, msgB.value)]
})

const showVoteHint = computed(() => exchanges.value < REQUIRED_EXCHANGES && !voted.value)
const exchangesLeft = computed(() => Math.max(0, REQUIRED_EXCHANGES - exchanges.value))
const showVotePanel = computed(() => exchanges.value >= REQUIRED_EXCHANGES && !voted.value)
const sendDisabled = computed(() => sending.value || !input.value.trim())

const resultText = computed(() => {
  if (!voted.value || !botA.value || !botB.value) return ''
  const names = `A: ${botA.value.name} / B: ${botB.value.name}`
  if (voted.value === 'A' || voted.value === 'B') {
    const b = voted.value === 'A' ? botA.value : botB.value
    return `「${b.name}」(${b.owner})に投票しました。${names}`
  }
  if (voted.value === 'tie') return `引き分けとして記録しました。${names}`
  return `どちらも微妙として記録しました。${names}`
})

function sendPrompt() {
  const text = input.value.trim()
  if (!text || sending.value) return

  const seed = exchanges.value
  const a = botA.value
  const b = botB.value

  // 各欄のメッセージは { role: 'user' | 'bot' | 'typing', text }。
  // 自分の質問を両方の欄に出し、その下に入力中の表示を置いて、回答が来たら置き換える
  msgA.value.push({ role: 'user', text }, { role: 'typing' })
  msgB.value.push({ role: 'user', text }, { role: 'typing' })
  input.value = ''
  sending.value = true

  schedule(
    () => {
      msgA.value.splice(-1, 1, { role: 'bot', text: pickResponse(a.category, seed) })
    },
    900 + Math.random() * 500,
  )

  schedule(
    () => {
      msgB.value.splice(-1, 1, { role: 'bot', text: pickResponse(b.category, seed + 1) })
      sending.value = false
      exchanges.value += 1
    },
    1500 + Math.random() * 500,
  )
}

function vote(choice) {
  if (voted.value) return
  voted.value = choice
}
</script>
