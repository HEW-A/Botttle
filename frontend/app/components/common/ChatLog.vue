<!--
  チャットのメッセージを並べるスクロール欄。
  中身(吹き出し)が増えたり変わったりしたら、自動で一番下までスクロールする。
  スクロールの高さは親で決める(親を flex の縦並びにし、この欄は残りの高さいっぱいに広がる)。
-->
<script setup lang="ts">
const logEl = ref<HTMLElement | null>(null)
let observer: MutationObserver | null = null

function scrollToBottom(smooth: boolean) {
  const el = logEl.value
  if (!el) return
  // 動きを減らす設定の人には、アニメーションせずに移動する
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  el.scrollTo({ top: el.scrollHeight, behavior: smooth && !reduceMotion ? 'smooth' : 'auto' })
}

onMounted(() => {
  scrollToBottom(false)
  if (!logEl.value) return
  // 中身の変化(吹き出しの追加、入力中の表示が回答に置き換わる など)を見張る
  observer = new MutationObserver(() => scrollToBottom(true))
  observer.observe(logEl.value, { childList: true, subtree: true, characterData: true })
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})
</script>

<template>
  <div ref="logEl" role="log" class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
    <slot />
  </div>
</template>
