<!-- ボットの「入力中」表示（ピル型の中にドット 3 つ）。avatar は ChatBubble と同じ -->
<script setup lang="ts">
withDefaults(defineProps<{ avatar?: string }>(), {
  avatar: undefined,
})
</script>

<template>
  <div class="flex items-center gap-2" role="status" aria-label="入力中">
    <span
      v-if="avatar"
      aria-hidden="true"
      class="flex size-7 flex-none items-center justify-center rounded-full bg-primary-100 text-xs font-bold text-primary-700"
    >
      {{ avatar }}
    </span>
    <span class="flex items-center gap-1.5 rounded-bubble border border-slate-200 bg-white px-4 py-3" aria-hidden="true">
      <span class="typing-dot size-1.5 rounded-full bg-slate-500" />
      <span class="typing-dot size-1.5 rounded-full bg-slate-500 [animation-delay:200ms]" />
      <span class="typing-dot size-1.5 rounded-full bg-slate-500 [animation-delay:400ms]" />
    </span>
  </div>
</template>

<style scoped>
.typing-dot {
  animation: typing-dot 1.2s infinite;
}

@keyframes typing-dot {
  0%,
  80%,
  100% {
    opacity: 0.25;
  }
  40% {
    opacity: 1;
  }
}
</style>
