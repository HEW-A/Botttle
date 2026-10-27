<template>
  <div class="font-['M_PLUS_1_Code']">
    <div class="mx-auto max-w-[1080px] px-6 pt-10 pb-16">
      <!-- ステップ表示 -->
      <div class="mb-8 flex items-center justify-end gap-2 text-xs text-slate-400">
        <template v-for="(label, i) in STEP_LABELS" :key="label">
          <span v-if="i > 0">›</span>
          <span class="font-semibold" :class="stepIndex === i + 1 ? 'text-blue-600' : 'text-slate-400'">
            {{ i + 1 }} {{ label }}
          </span>
        </template>
      </div>

      <!-- ============ モード選択 ============ -->
      <template v-if="step === 'mode'">
        <div class="mb-8 text-center">
          <h1 class="mb-2.5 text-[28px] font-bold text-slate-800">対戦方法を選ぶ</h1>
          <p class="text-sm leading-relaxed text-slate-500">
            2体のボットに同じ質問を送り、良い回答をした方に投票します。
          </p>
        </div>
        <div class="mx-auto grid max-w-[760px] grid-cols-1 gap-5 sm:grid-cols-2">
          <button
            type="button"
            class="flex cursor-pointer flex-col gap-3 rounded-[14px] border border-slate-200 bg-white p-7 text-left hover:border-blue-600"
            @click="goRandom"
          >
            <span class="text-xs font-semibold text-blue-600">匿名バトル</span>
            <span class="text-[22px] font-bold text-slate-800">ランダム</span>
            <span class="text-[13px] leading-relaxed text-slate-500">
              出品中のボットから2体をランダムに選出。名前は投票後に公開されます。
            </span>
            <span class="mt-2 self-start rounded-lg bg-blue-600 px-5 py-2.5 text-[13px] font-bold text-white">
              すぐに対戦する
            </span>
          </button>
          <button
            type="button"
            class="flex cursor-pointer flex-col gap-3 rounded-[14px] border border-slate-200 bg-white p-7 text-left hover:border-slate-700"
            @click="goPick"
          >
            <span class="text-xs font-semibold text-slate-700">指名バトル</span>
            <span class="text-[22px] font-bold text-slate-800">選ぶ</span>
            <span class="text-[13px] leading-relaxed text-slate-500">
              検索・お気に入り・カテゴリからAとBのボットを自分で指定して比較します。
            </span>
            <span class="mt-2 self-start rounded-lg bg-slate-700 px-5 py-2.5 text-[13px] font-bold text-white">
              ボットを選ぶ
            </span>
          </button>
        </div>
      </template>

      <!-- ============ ボット選択 ============ -->
      <template v-else-if="step === 'pick'">
        <div class="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 class="mb-1.5 text-2xl font-bold text-slate-800">対戦するボットを選ぶ</h1>
            <p class="text-[13px] text-slate-500">AとBそれぞれに1体ずつ選択してください</p>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-lg border border-slate-300 bg-white px-4 py-2 text-[13px] font-semibold whitespace-nowrap text-slate-700 hover:bg-slate-100"
            @click="backToMode"
          >
            戻る
          </button>
        </div>

        <div class="mb-7 grid grid-cols-1 gap-5 md:grid-cols-2">
          <div
            v-for="side in sideViews"
            :key="side.key"
            class="flex flex-col gap-3.5 rounded-[14px] border border-slate-200 bg-white p-5"
          >
            <div class="flex items-center justify-between gap-2.5">
              <div class="flex items-center gap-2.5">
                <div
                  class="flex h-9 w-9 items-center justify-center rounded-full bg-slate-700 text-base font-bold text-white"
                >
                  {{ side.key }}
                </div>
                <span class="text-base font-bold text-slate-800">ボット {{ side.key }}</span>
              </div>
              <span
                v-if="side.state.selected"
                class="max-w-[180px] truncate rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-600"
              >
                {{ side.state.selected.name }}
              </span>
            </div>

            <input
              v-model="side.state.query"
              type="text"
              placeholder="ボット名・出品者で検索"
              class="rounded-lg border border-slate-300 bg-white px-3.5 py-[11px] text-[13px] text-slate-800 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-blue-600"
            />

            <div class="grid grid-cols-2 gap-2.5">
              <button
                type="button"
                class="rounded-lg border p-2.5 text-[13px] font-semibold"
                :class="toggleClass(side.state.favOnly)"
                @click="side.state.favOnly = !side.state.favOnly"
              >
                お気に入りから選択
              </button>
              <button
                type="button"
                class="rounded-lg border p-2.5 text-[13px] font-semibold"
                :class="toggleClass(side.state.showCats || !!side.state.cat)"
                @click="toggleCats(side.state)"
              >
                カテゴリから検索
              </button>
            </div>

            <div v-if="side.state.showCats" class="flex flex-wrap gap-1.5">
              <button
                v-for="c in CATEGORIES"
                :key="c"
                type="button"
                class="shrink-0 rounded-full border px-3 py-[5px] text-xs font-medium whitespace-nowrap"
                :class="
                  side.state.cat === c
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : 'border-slate-300 bg-white text-slate-700'
                "
                @click="side.state.cat = side.state.cat === c ? null : c"
              >
                {{ c }}
              </button>
            </div>

            <div class="flex h-[300px] flex-col gap-1.5 overflow-y-auto pr-0.5">
              <button
                v-for="bot in side.results"
                :key="bot.id"
                type="button"
                :disabled="bot.taken"
                class="flex items-center gap-3 rounded-[10px] border px-3 py-2.5 text-left hover:border-blue-600 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-slate-200"
                :class="bot.selected ? 'border-blue-600 bg-blue-50' : 'border-slate-200 bg-white'"
                @click="side.state.selected = bot.selected ? null : bot"
              >
                <div
                  class="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-full bg-slate-700 text-[13px] font-bold text-white"
                >
                  {{ bot.avatar }}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="truncate text-[13px] font-bold text-slate-800">{{ bot.name }}</div>
                  <div class="text-[11px] text-slate-400">{{ bot.owner }} ・ {{ bot.category }}</div>
                </div>
                <span v-if="bot.fav" class="shrink-0 text-[11px] text-amber-500">★</span>
              </button>
              <p v-if="!side.results.length" class="my-6 text-center text-[13px] text-slate-400">
                該当するボットがありません
              </p>
            </div>
          </div>
        </div>

        <div class="flex justify-center">
          <button
            type="button"
            :disabled="!canStart"
            class="rounded-[10px] px-10 py-3.5 text-[15px] font-bold text-white"
            :class="canStart ? 'bg-blue-600 hover:bg-blue-700' : 'cursor-not-allowed bg-slate-400'"
            @click="startPicked"
          >
            アリーナへ進む
          </button>
        </div>
      </template>

      <!-- ============ アリーナ ============ -->
      <template v-else>
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 class="mb-1 text-xl font-bold text-slate-800">
              {{ mode === 'random' ? 'アリーナ ・ ランダム対戦' : 'アリーナ ・ 指名対戦' }}
            </h1>
            <p class="text-[13px] text-slate-500">
              {{
                mode === 'random' ? 'ボットの正体は投票後に公開されます' : '同じ質問を両方のボットに送って比較しましょう'
              }}
            </p>
          </div>
          <button
            type="button"
            class="shrink-0 rounded-lg border border-slate-300 bg-white px-4 py-2 text-[13px] font-semibold whitespace-nowrap text-slate-700 hover:bg-slate-100"
            @click="backToMode"
          >
            対戦をやめる
          </button>
        </div>

        <div v-if="promptLog.length" class="mb-4 flex flex-col gap-1.5">
          <div
            v-for="(p, i) in promptLog"
            :key="i"
            class="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-[13px] text-blue-700"
          >
            Q. {{ p.text }}
          </div>
        </div>

        <div class="mb-5 grid grid-cols-1 gap-4 md:grid-cols-2">
          <div
            v-for="pn in panels"
            :key="pn.key"
            class="flex h-[420px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white"
          >
            <div class="flex items-center gap-2.5 border-b border-slate-200 px-4 py-3.5">
              <div
                class="flex h-[34px] w-[34px] flex-none items-center justify-center rounded-full text-[13px] font-bold text-white"
                :class="pn.anon ? 'bg-slate-700' : 'bg-blue-600'"
              >
                {{ pn.avatar }}
              </div>
              <div class="min-w-0">
                <div class="text-[13px] font-bold text-slate-800">{{ pn.name }}</div>
                <div class="text-[11px] text-slate-400">{{ pn.owner }}</div>
              </div>
            </div>
            <div class="flex flex-1 flex-col gap-2.5 overflow-y-auto p-4">
              <template v-for="(msg, i) in pn.messages" :key="i">
                <div
                  v-if="msg.isText"
                  class="max-w-[90%] rounded-[10px] bg-slate-100 px-3 py-2.5 text-[13px] leading-relaxed text-slate-800"
                >
                  {{ msg.text }}
                </div>
                <div v-else class="inline-flex w-fit gap-1 rounded-[10px] bg-slate-100 px-3.5 py-2.5">
                  <span class="ba-dot h-1.5 w-1.5 rounded-full bg-slate-400" style="animation-delay: 0ms"></span>
                  <span class="ba-dot h-1.5 w-1.5 rounded-full bg-slate-400" style="animation-delay: 200ms"></span>
                  <span class="ba-dot h-1.5 w-1.5 rounded-full bg-slate-400" style="animation-delay: 400ms"></span>
                </div>
              </template>
            </div>
          </div>
        </div>

        <div class="mb-5 flex gap-2.5">
          <input
            v-model="input"
            type="text"
            :disabled="sending"
            placeholder="両方のボットに送る質問を入力…"
            class="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-[13px] text-slate-800 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-blue-600"
            @keydown.enter="onEnter"
          />
          <button
            type="button"
            :disabled="sendDisabled"
            class="rounded-lg px-[22px] py-3 text-[13px] font-bold text-white"
            :class="sendDisabled ? 'cursor-not-allowed bg-slate-400' : 'bg-blue-600 hover:bg-blue-700'"
            @click="sendPrompt"
          >
            {{ sending ? '送信中…' : '送信' }}
          </button>
        </div>

        <p v-if="showVoteHint" class="mb-6 text-center text-xs text-slate-400">
          あと{{ exchangesLeft }}回のやり取りで投票が可能になります
        </p>

        <div v-if="showVotePanel" class="mb-5 rounded-xl border border-slate-200 bg-white p-5">
          <h3 class="mb-3.5 text-center text-sm font-bold text-slate-800">どちらの回答が良かった？</h3>
          <div class="flex flex-wrap justify-center gap-2.5">
            <button
              v-for="v in VOTE_DEFS"
              :key="v.key"
              type="button"
              class="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-[13px] font-semibold text-slate-700 hover:border-blue-600 hover:bg-blue-600 hover:text-white"
              @click="vote(v.key)"
            >
              {{ v.label }}
            </button>
          </div>
        </div>

        <div v-if="voted" class="rounded-xl border border-blue-200 bg-blue-50 p-[22px] text-center">
          <p class="mb-1.5 text-[13px] font-bold text-blue-700">投票ありがとうございます</p>
          <p class="mb-[18px] text-[13px] text-slate-700">{{ resultText }}</p>
          <div class="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              class="rounded-lg bg-blue-600 px-[22px] py-2.5 text-[13px] font-bold text-white hover:bg-blue-700"
              @click="rematch"
            >
              もう一度対戦する
            </button>
            <button
              type="button"
              class="rounded-lg border border-slate-300 bg-white px-[22px] py-2.5 text-[13px] font-semibold text-slate-700 hover:bg-slate-100"
              @click="backToMode"
            >
              モード選択へ
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// BotArena: 2体のボットに同じ質問を送って回答を比較し、投票するバトル機能。
// 対戦方法は「ランダム(匿名)」と「選ぶ(指名)」の二択。ランダムは投票後に正体を公開する。
// バックエンドAPIが未実装のため、本ページはダミーデータ・擬似応答によるフロントエンド単体のモックアップ。
// ヘッダー/フッターは共通レイアウト(layouts/default.vue)側が描画するため、ここでは持たない。

useHead({
  title: 'BotArena | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

// 対戦に必要なやり取り回数(これに達すると投票パネルが表示される)
const REQUIRED_EXCHANGES = 2

const STEP_LABELS = ['モード', 'ボット選択', 'アリーナ']

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
const promptLog = ref([])
const msgA = ref([])
const msgB = ref([])
const exchanges = ref(0)
const voted = ref(null) // null | 'A' | 'B' | 'tie' | 'bad'
const sending = ref(false)

const stepIndex = computed(() => ({ mode: 1, pick: 2, arena: 3 })[step.value])

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

function toggleClass(active) {
  return active ? 'border-slate-700 bg-slate-700 text-white' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
}

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
  mode.value = nextMode
  botA.value = a
  botB.value = b
  input.value = ''
  promptLog.value = []
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
  // ランダム対戦は投票まで匿名
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

function onEnter(e) {
  // IME変換確定のEnterでは送信しない
  if (e.isComposing) return
  sendPrompt()
}

function sendPrompt() {
  const text = input.value.trim()
  if (!text || sending.value) return

  const seed = exchanges.value
  const a = botA.value
  const b = botB.value

  promptLog.value.push({ text })
  msgA.value.push({ isText: false })
  msgB.value.push({ isText: false })
  input.value = ''
  sending.value = true

  setTimeout(
    () => {
      msgA.value.splice(-1, 1, { isText: true, text: pickResponse(a.category, seed) })
    },
    900 + Math.random() * 500,
  )

  setTimeout(
    () => {
      msgB.value.splice(-1, 1, { isText: true, text: pickResponse(b.category, seed + 1) })
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

<style scoped>
@keyframes ba-blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
.ba-dot {
  animation: ba-blink 1.2s infinite;
}
</style>
