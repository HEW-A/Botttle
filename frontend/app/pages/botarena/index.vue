<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <CommonAppHeader />

    <main class="flex-1">
      <div class="mx-auto max-w-5xl px-6 py-10 md:py-14">
        <!-- ============ ボット選択 ============ -->
        <template v-if="step === 'select'">
          <div class="mb-7">
            <h1 class="mb-2 text-2xl font-bold text-slate-900">BotArenaに参戦する</h1>
            <p class="mb-4 text-sm leading-relaxed text-slate-500">
              匿名の2体のチャットボットに同じ質問を投げかけ、良い回答をした方に投票するバトル形式です。相手の正体は投票後に公開されます。
            </p>
            <div class="flex flex-wrap gap-6 rounded-xl border border-slate-200 bg-white px-5 py-4">
              <div class="text-[13px] text-slate-700"><b class="text-blue-600">1.</b> 出品中のボットを選ぶ</div>
              <div class="text-[13px] text-slate-700"><b class="text-blue-600">2.</b> 同じ質問を両方に送る</div>
              <div class="text-[13px] text-slate-700"><b class="text-blue-600">3.</b> 良い回答に投票し、正体を確認</div>
            </div>
          </div>

          <h2 class="mb-3 text-[15px] font-bold text-slate-700">参戦させるボットを選択</h2>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="bot in MY_BOTS"
              :key="bot.id"
              class="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-[18px]"
            >
              <div class="flex items-center gap-3">
                <div
                  class="flex h-10 w-10 flex-none items-center justify-center rounded-full bg-slate-700 text-[15px] font-bold text-white"
                >
                  {{ bot.avatar }}
                </div>
                <div class="min-w-0">
                  <div class="truncate text-sm font-bold text-slate-900">{{ bot.name }}</div>
                  <div class="text-xs text-slate-400">{{ bot.category }}</div>
                </div>
              </div>
              <div class="flex gap-4 text-xs text-slate-500">
                <span>勝率 <b class="text-slate-700">{{ bot.winRate }}%</b></span>
                <span>対戦数 <b class="text-slate-700">{{ bot.battles }}</b></span>
              </div>
              <button
                type="button"
                class="mt-1 w-full rounded-lg bg-blue-600 py-2.5 text-[13px] font-semibold text-white hover:bg-blue-700"
                @click="startBattle(bot)"
              >
                このボットで参戦
              </button>
            </div>
          </div>
        </template>

        <!-- ============ 対戦 ============ -->
        <template v-else>
          <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h1 class="mb-1 text-xl font-bold text-slate-900">対戦中</h1>
              <p class="text-[13px] text-slate-500">対戦相手の正体は投票後に公開されます</p>
            </div>
            <button
              type="button"
              class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-[13px] font-semibold text-slate-700 hover:bg-slate-100"
              @click="quitBattle"
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
            <!-- 左パネル -->
            <div class="flex h-[420px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div class="flex items-center gap-2.5 border-b border-slate-200 px-4 py-3.5">
                <div
                  class="flex h-[34px] w-[34px] flex-none items-center justify-center rounded-full text-[13px] font-bold text-white"
                  :class="voted ? 'bg-blue-600' : 'bg-slate-700'"
                >
                  {{ leftAvatarLabel }}
                </div>
                <div class="min-w-0">
                  <div class="text-[13px] font-bold text-slate-900">{{ leftName }}</div>
                  <div v-if="voted" class="text-[11px] text-slate-400">{{ leftOwner }}</div>
                </div>
              </div>
              <div class="flex flex-1 flex-col gap-2.5 overflow-y-auto p-4">
                <template v-for="(msg, i) in messagesLeft" :key="i">
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

            <!-- 右パネル -->
            <div class="flex h-[420px] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white">
              <div class="flex items-center gap-2.5 border-b border-slate-200 px-4 py-3.5">
                <div
                  class="flex h-[34px] w-[34px] flex-none items-center justify-center rounded-full text-[13px] font-bold text-white"
                  :class="voted ? 'bg-blue-600' : 'bg-slate-700'"
                >
                  {{ rightAvatarLabel }}
                </div>
                <div class="min-w-0">
                  <div class="text-[13px] font-bold text-slate-900">{{ rightName }}</div>
                  <div v-if="voted" class="text-[11px] text-slate-400">{{ rightOwner }}</div>
                </div>
              </div>
              <div class="flex flex-1 flex-col gap-2.5 overflow-y-auto p-4">
                <template v-for="(msg, i) in messagesRight" :key="i">
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

          <div class="mb-6 flex gap-2.5">
            <input
              v-model="input"
              type="text"
              :disabled="sending"
              placeholder="両方のボットに送る質問を入力…"
              class="flex-1 rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-[13px] text-slate-900 focus:border-blue-600 focus:outline focus:outline-2 focus:outline-blue-600"
              @keydown.enter="sendPrompt"
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
            <h3 class="mb-3.5 text-center text-sm font-bold text-slate-900">どちらの回答が良かった？</h3>
            <div class="flex flex-wrap justify-center gap-2.5">
              <button
                v-for="v in voteButtons"
                :key="v.key"
                type="button"
                class="rounded-full border px-5 py-2.5 text-[13px] font-semibold"
                :class="
                  v.active
                    ? 'border-blue-600 bg-blue-600 text-white'
                    : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                "
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
                @click="quitBattle"
              >
                ボットを選び直す
              </button>
            </div>
          </div>
        </template>
      </div>
    </main>

    <CommonAppFooter />
  </div>
</template>

<script setup>
// BotArena: 匿名の2ボットに同じ質問を送って回答を比較し、投票後に正体を公開するバトル機能。
// バックエンドAPIが未実装のため、本ページはダミーデータ・擬似応答によるフロントエンド単体のモックアップ。
definePageMeta({
  layout: false,
})

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
// 自分のボットが左右どちらに表示されるかをランダム化するか
const RANDOMIZE_SIDES = true

const MY_BOTS = [
  { id: 'm1', name: '家計簿アシスタント クレバー', category: '家計管理', avatar: 'ク', winRate: 62, battles: 14 },
  { id: 'm2', name: '英会話パートナー トーキー', category: '語学', avatar: 'ト', winRate: 70, battles: 9 },
  { id: 'm3', name: '献立提案ロボ ククル', category: '料理', avatar: 'ク', winRate: 58, battles: 5 },
]

const OPPONENT_POOL = [
  { id: 'b1', name: 'レシピ相談員 ポタージュ', owner: '@yuki_cook', category: '料理', avatar: 'ポ', winRate: 68 },
  { id: 'b2', name: '旅程プランナー オデッセイ', owner: '@tabi_taro', category: '旅行', avatar: 'オ', winRate: 74 },
  { id: 'b3', name: '法律クイックQA リーガルビット', owner: '@legal_min', category: '法律', avatar: 'リ', winRate: 55 },
  { id: 'b4', name: '筋トレコーチ マッスルナビ', owner: '@fit_coach', category: 'フィットネス', avatar: 'マ', winRate: 81 },
]

const RESPONSES = {
  家計管理: ['固定費を先取りで管理すると、月末の変動費に余裕が生まれますよ。', 'まずは1週間だけレシートを記録して、支出の傾向を見てみましょう。'],
  語学: ['その表現は少しフォーマルすぎるかもしれません。カジュアルな場では別の言い回しがおすすめです。', '発音のコツは口をやや大きく開けることです。何度か声に出してみましょう。'],
  料理: ['旬の食材を使うと風味が引き立ちます。下味に塩と少量の酒を使うのがポイントです。', '火加減は中火をキープしつつ、途中で一度混ぜると失敗しにくいですよ。'],
  旅行: ['乾季のこの時期は朝夕が冷えるので、薄手の羽織りがあると安心です。', '移動時間を短くするなら、拠点を1つに固めるプランがおすすめです。'],
  法律: ['一般的な見解としては、契約書に明記がない場合は民法の規定が適用されます。', '個別の事情によって結論が変わるため、専門家への相談も検討してください。'],
  フィットネス: ['まずはフォームを固めることが先です。回数より質を優先しましょう。', '週2回のペースから始めて、体の反応を見ながら調整していきましょう。'],
  default: ['なるほど、その内容について整理しますね。まず前提を確認すると…', 'ご質問ありがとうございます。ポイントは大きく2つあります。'],
}

function pickResponse(category, seed) {
  const list = RESPONSES[category] || RESPONSES.default
  return list[seed % list.length]
}

const step = ref('select') // 'select' | 'battle'
const myBot = ref(null)
const opponent = ref(null)
const leftIsMine = ref(true)
const input = ref('')
const promptLog = ref([])
const messagesLeft = ref([])
const messagesRight = ref([])
const exchanges = ref(0)
const voted = ref(null) // null | 'A' | 'B' | 'tie' | 'bad'
const sending = ref(false)

const leftBot = computed(() => (leftIsMine.value ? myBot.value : opponent.value))
const rightBot = computed(() => (leftIsMine.value ? opponent.value : myBot.value))

const leftAvatarLabel = computed(() => (voted.value && leftBot.value ? leftBot.value.avatar : 'A'))
const rightAvatarLabel = computed(() => (voted.value && rightBot.value ? rightBot.value.avatar : 'B'))
const leftName = computed(() => (voted.value && leftBot.value ? leftBot.value.name : 'Bot A'))
const rightName = computed(() => (voted.value && rightBot.value ? rightBot.value.name : 'Bot B'))
const leftOwner = computed(() => (leftBot.value ? leftBot.value.owner || '(あなたのボット)' : ''))
const rightOwner = computed(() => (rightBot.value ? rightBot.value.owner || '(あなたのボット)' : ''))

const showVoteHint = computed(() => exchanges.value < REQUIRED_EXCHANGES && !voted.value)
const exchangesLeft = computed(() => Math.max(0, REQUIRED_EXCHANGES - exchanges.value))
const showVotePanel = computed(() => exchanges.value >= REQUIRED_EXCHANGES && !voted.value)
const sendDisabled = computed(() => sending.value || !input.value.trim())

const VOTE_DEFS = [
  { key: 'A', label: 'Aが良い' },
  { key: 'B', label: 'Bが良い' },
  { key: 'tie', label: '引き分け' },
  { key: 'bad', label: 'どちらも微妙' },
]
const voteButtons = computed(() => VOTE_DEFS.map((v) => ({ ...v, active: voted.value === v.key })))

const resultText = computed(() => {
  if (voted.value === 'A') return `「${leftBot.value?.name ?? ''}」に投票しました。出品者: ${leftBot.value?.owner || '(あなた)'}`
  if (voted.value === 'B') return `「${rightBot.value?.name ?? ''}」に投票しました。出品者: ${rightBot.value?.owner || '(あなた)'}`
  if (voted.value === 'tie') return '引き分けとして記録しました。両者の正体を公開します。'
  if (voted.value === 'bad') return 'どちらも今回は微妙、という評価で記録しました。'
  return ''
})

function startBattle(bot) {
  const nextOpponent = OPPONENT_POOL[Math.floor(Math.random() * OPPONENT_POOL.length)]
  myBot.value = bot
  opponent.value = nextOpponent
  leftIsMine.value = RANDOMIZE_SIDES ? Math.random() < 0.5 : true
  input.value = ''
  promptLog.value = []
  messagesLeft.value = []
  messagesRight.value = []
  exchanges.value = 0
  voted.value = null
  sending.value = false
  step.value = 'battle'
}

function quitBattle() {
  step.value = 'select'
  voted.value = null
}

function rematch() {
  if (myBot.value) startBattle(myBot.value)
}

function sendPrompt() {
  const text = input.value.trim()
  if (!text || sending.value) return

  const seed = exchanges.value
  const leftB = leftBot.value
  const rightB = rightBot.value

  promptLog.value.push({ text })
  messagesLeft.value.push({ isText: false })
  messagesRight.value.push({ isText: false })
  input.value = ''
  sending.value = true

  setTimeout(
    () => {
      messagesLeft.value.splice(-1, 1, { isText: true, text: pickResponse(leftB.category, seed) })
    },
    900 + Math.random() * 500,
  )

  setTimeout(
    () => {
      messagesRight.value.splice(-1, 1, { isText: true, text: pickResponse(rightB.category, seed + 1) })
      sending.value = false
      exchanges.value += 1
    },
    1400 + Math.random() * 500,
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
