<template>
  <CommonPageContainer size="narrow">
    <CommonPageHeader title="チャットボットを作成" description="PDFファイルをアップロードすると、その内容をもとにチャットボットを作成します。" />

    <div class="mb-9 flex flex-col gap-2.5">
      <!-- クリックでもキーボード(Enter/Space)でもファイルを選べるよう button にしている -->
      <button
        type="button"
        class="flex min-h-38 w-full cursor-pointer flex-col items-center justify-center gap-2.5 border-2 border-dashed transition-colors focus-visible:outline-2 focus-visible:outline-primary"
        :class="dragOver ? 'border-primary bg-primary-50' : 'border-slate-300 bg-white hover:border-primary'"
        @click="openPicker"
        @drop.prevent="handleDrop"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
      >
        <svg class="text-primary" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 3v12"></path>
          <path d="M7 8l5-5 5 5"></path>
          <path d="M4 17v3a2 2 0 002 2h12a2 2 0 002-2v-3"></path>
        </svg>
        <span class="text-base font-bold text-slate-900">PDFをアップロード</span>
        <span class="text-xs text-slate-500">またはドラッグ&amp;ドロップ</span>
      </button>
      <input
        ref="fileInputRef"
        type="file"
        multiple
        accept=".pdf,application/pdf"
        class="hidden"
        @change="handleFileChange"
      />

      <div
        v-for="(file, index) in displayFiles"
        :key="`${file.name}-${index}`"
        class="flex items-center justify-between gap-2 border border-slate-200 bg-white py-1.5 pr-1.5 pl-3.5"
      >
        <div class="flex min-w-0 items-center gap-2.5">
          <span class="flex-none border border-primary px-1.5 py-0.5 text-xs font-bold tracking-wide text-primary">{{ file.ext }}</span>
          <span class="truncate text-sm text-slate-900">{{ file.name }}</span>
          <span class="flex-none text-xs text-slate-500">{{ file.sizeLabel }}</span>
        </div>
        <UButton color="neutral" variant="ghost" size="sm" square class="flex-none" :aria-label="`${file.name}を取り除く`" @click="removeFile(index)">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </UButton>
      </div>

      <p v-if="createError" class="text-sm font-bold text-red-600" role="alert">
        {{ createError }}
      </p>
    </div>

    <UButton block size="lg" :disabled="!canCreate" @click="createBot">チャットボットを作成する</UButton>

    <!-- 作成中(閉じられない) -->
    <UModal
      :open="stage === 'creating'"
      title="チャットボットを作成しています"
      :dismissible="false"
      :close="false"
      :ui="{ content: 'sm:max-w-sm' }"
    >
      <template #content>
        <div class="flex flex-col items-center gap-4 px-12 py-10" role="status">
          <div class="size-9 animate-spin rounded-full border-4 border-slate-200 border-t-primary" aria-hidden="true"></div>
          <span class="text-base font-bold text-slate-900">チャットボットを作成しています...</span>
          <span class="text-xs text-slate-500">しばらくお待ちください</span>
        </div>
      </template>
    </UModal>

    <!-- 作成完了(閉じると最初の状態に戻る) -->
    <UModal
      :open="stage === 'created'"
      title="チャットボットが完成しました"
      :ui="{ content: 'sm:max-w-md' }"
      @update:open="(open) => { if (!open) closeModal() }"
    >
      <template #content>
        <div class="relative flex flex-col items-center gap-4 px-10 py-11">
          <UButton color="neutral" variant="ghost" size="sm" square aria-label="閉じる" class="absolute top-3 right-3" @click="closeModal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </UButton>
          <div class="flex size-13 items-center justify-center rounded-full border-2 border-primary text-primary">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20 6L9 17l-5-5"></path>
            </svg>
          </div>
          <div class="flex flex-col items-center gap-1.5 text-center">
            <p class="text-xl font-bold text-slate-900" aria-hidden="true">チャットボットが完成しました</p>
            <p class="text-sm leading-relaxed text-slate-500">作成したチャットボットを出品するか、動作をテストできます。</p>
            <p v-if="creationWarning" class="text-xs leading-relaxed font-bold text-amber-700" role="alert">
              {{ creationWarning }}
            </p>
          </div>
          <div class="mt-1.5 flex w-full gap-2.5">
            <UButton variant="outline" class="flex-1 justify-center" @click="goToTest">テストする</UButton>
            <UButton class="flex-1 justify-center" @click="goToListing">出品する</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </CommonPageContainer>
</template>

<script setup>
definePageMeta({
  middleware: 'auth',
})

const router = useRouter()
const config = useRuntimeConfig()

useHead({
  title: 'チャットボットを作成 | botttle',
})

const fileInputRef = ref(null)
const files = ref([])
const stage = ref('setup') // 'setup' | 'creating' | 'created'
const dragOver = ref(false)
const createdChatbotId = ref('')
const createError = ref('')
const creationWarning = ref('')

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
  const accepted = Array.from(fileList || []).filter((file) => /\.pdf$/i.test(file.name))
  if (!accepted.length) {
    createError.value = 'PDFファイルを選択してください。'
    return
  }

  createError.value = ''
  files.value = [...files.value, ...accepted]
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

async function createBot() {
  if (!canCreate.value) return

  stage.value = 'creating'
  createError.value = ''
  creationWarning.value = ''
  createdChatbotId.value = ''

  const formData = new FormData()
  const initialBotName = files.value[0].name.replace(/\.pdf$/i, '').trim() || '新しいチャットボット'
  formData.append('bot_name', initialBotName.slice(0, 40))
  files.value.forEach((file) => formData.append('files', file))

  try {
    const result = await $fetch('/api/bots', {
      baseURL: config.public.apiBase,
      method: 'POST',
      credentials: 'include',
      body: formData,
    })

    if (!result.chatbot_id) {
      throw new Error('作成したチャットボットのIDを取得できませんでした。')
    }

    createdChatbotId.value = result.chatbot_id
    if (result.failed?.length) {
      const details = result.failed
        .map((item) => `${item.file_name}: ${item.reason}`)
        .join('、')
      creationWarning.value = `一部のPDFを保存できませんでした。${details}`
    }
    stage.value = 'created'
  } catch (error) {
    const message = error?.data?.error || error?.message || 'チャットボットの作成に失敗しました。'
    const details = error?.data?.failed
      ?.map((item) => `${item.file_name}: ${item.reason}`)
      .join('、')
    createError.value = details ? `${message}（${details}）` : message
    stage.value = 'setup'
  }
}

function closeModal() {
  stage.value = 'setup'
  files.value = []
  createdChatbotId.value = ''
  createError.value = ''
  creationWarning.value = ''
}

function goToTest() {
  if (createdChatbotId.value) {
    router.push(`/chatbot/${createdChatbotId.value}/test`)
  }
}

function goToListing() {
  if (createdChatbotId.value) {
    router.push(`/chatbot/${createdChatbotId.value}/listing`)
  }
}
</script>
