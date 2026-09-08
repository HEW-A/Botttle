<template>
  <div class="flex min-h-screen flex-col bg-slate-50 font-['M_PLUS_1_Code']">
    <commonAppHeader/>

    <main class="flex-1">
      <div class="mx-auto flex w-full max-w-[640px] flex-col gap-9 px-6 py-14">
        <div class="flex flex-col gap-1.5">
          <h1 class="text-2xl font-bold text-slate-900">チャットボットを作成</h1>
          <p class="text-sm leading-relaxed text-slate-500">
            PDFまたはtxt形式のファイルをアップロードすると、その内容をもとにチャットボットを作成します。
          </p>
        </div>

        <div class="flex flex-col gap-2.5">
          <div
            class="flex min-h-[150px] cursor-pointer flex-col items-center justify-center gap-2.5 border-2 transition-colors"
            :class="dragOver ? 'border-blue-600 bg-blue-50' : 'border-slate-900 bg-white'"
            @click="openPicker"
            @drop.prevent="handleDrop"
            @dragover.prevent="dragOver = true"
            @dragleave="dragOver = false"
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#0f172a" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3v12"></path>
              <path d="M7 8l5-5 5 5"></path>
              <path d="M4 17v3a2 2 0 002 2h12a2 2 0 002-2v-3"></path>
            </svg>
            <span class="text-[15px] font-bold text-slate-900">PDF、txtをアップロード</span>
            <span class="text-xs text-slate-400">またはドラッグ&amp;ドロップ</span>
            <input
              ref="fileInputRef"
              type="file"
              multiple
              accept=".pdf,.txt"
              class="hidden"
              @change="handleFileChange"
            />
          </div>

          <div
            v-for="(file, index) in displayFiles"
            :key="`${file.name}-${index}`"
            class="flex items-center justify-between border border-slate-200 bg-white px-3.5 py-3"
          >
            <div class="flex min-w-0 items-center gap-2.5">
              <span class="flex-none border border-blue-600 px-1.5 py-0.5 text-[10px] font-bold tracking-wide text-blue-600">{{ file.ext }}</span>
              <span class="truncate text-[13px] text-slate-900">{{ file.name }}</span>
              <span class="flex-none text-xs text-slate-400">{{ file.sizeLabel }}</span>
            </div>
            <button type="button" class="flex-none px-1 text-lg leading-none text-slate-400" @click="removeFile(index)">&times;</button>
          </div>
        </div>

        <button
          type="button"
          class="w-full border-2 border-transparent py-4 text-[15px] font-bold"
          :class="canCreate ? 'cursor-pointer bg-blue-600 text-white' : 'cursor-not-allowed bg-slate-200 text-slate-400'"
          :disabled="!canCreate"
          @click="createBot"
        >
          チャットボットを作成する
        </button>
      </div>
    </main>

    <CommonAppFooter />

    <div v-if="stage === 'creating'" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60">
      <div class="flex flex-col items-center gap-4 border-2 border-slate-900 bg-white px-12 py-10">
        <div class="h-[34px] w-[34px] animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>
        <span class="text-[15px] font-semibold text-slate-900">チャットボットを作成しています...</span>
        <span class="text-xs text-slate-400">しばらくお待ちください</span>
      </div>
    </div>

    <div v-if="stage === 'created'" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-6">
      <div class="flex w-full max-w-[400px] flex-col items-center gap-[18px] border-2 border-slate-900 bg-white px-10 py-11">
        <div class="flex h-[52px] w-[52px] items-center justify-center rounded-full border-2 border-blue-600">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 6L9 17l-5-5"></path>
          </svg>
        </div>
        <div class="flex flex-col items-center gap-1.5 text-center">
          <h2 class="text-[19px] font-bold text-slate-900">チャットボットが完成しました</h2>
          <p class="text-[13px] leading-relaxed text-slate-500">作成したチャットボットを出品するか、動作をテストできます。</p>
        </div>
        <div class="mt-1.5 flex w-full gap-2.5">
          <button type="button" class="flex-1 border-2 border-slate-700 bg-white py-3 text-sm font-bold text-slate-700">テストする</button>
          <button type="button" class="flex-1 border-2 border-blue-600 bg-blue-600 py-3 text-sm font-bold text-white">出品する</button>
        </div>
        <button type="button" class="mt-0.5 p-1 text-xs text-slate-400" @click="closeModal">閉じる</button>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

const router = useRouter()

useHead({
  title: 'チャットボットを作成 | botttle',
  link: [
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=M+PLUS+1+Code:wght@400;500;600;700&display=swap',
    },
  ],
})

const CREATE_DELAY_MS = 2200

const fileInputRef = ref(null)
const files = ref([])
const stage = ref('setup') // 'setup' | 'creating' | 'created'
const dragOver = ref(false)

const canCreate = computed(() => files.value.length > 0)
const displayFiles = computed(() =>
  files.value.map((file) => ({
    name: file.name,
    ext: (file.name.split('.').pop() || '').toUpperCase(),
    sizeLabel: formatSize(file.size),
  })),
)

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function addFiles(fileList) {
  const accepted = Array.from(fileList || []).filter((file) => /\.(pdf|txt)$/i.test(file.name))
  if (!accepted.length) return
  files.value = [...files.value, ...accepted.map((file) => ({ name: file.name, size: file.size }))]
}

function handleFileChange(e) {
  addFiles(e.target.files)
  e.target.value = ''
}

function handleDrop(e) {
  dragOver.value = false
  addFiles(e.dataTransfer.files)
}

function removeFile(index) {
  files.value = files.value.filter((_, i) => i !== index)
}

function openPicker() {
  fileInputRef.value?.click()
}

function createBot() {
  if (!canCreate.value) return
  stage.value = 'creating'
  setTimeout(() => {
    stage.value = 'created'
  }, CREATE_DELAY_MS)
}

function closeModal() {
  stage.value = 'setup'
  files.value = []
}
</script>
