<!--
  チャットの吹き出し 1 件分。
  sender="user" … 右寄せ・primary の塗り
  sender="bot"  … 左寄せ・白地に枠線。avatar に 1 文字渡すと左に丸いアイコンを出す
-->
<script setup lang="ts">
withDefaults(
  defineProps<{
    sender: 'user' | 'bot'
    avatar?: string
  }>(),
  {
    avatar: undefined,
  },
)
</script>

<template>
  <div class="flex items-start gap-2" :class="sender === 'user' ? 'justify-end' : 'justify-start'">
    <span
      v-if="sender === 'bot' && avatar"
      aria-hidden="true"
      class="flex size-7 flex-none items-center justify-center rounded-full bg-primary-100 text-xs font-bold text-primary-700"
    >
      {{ avatar }}
    </span>
    <p
      class="m-0 max-w-[85%] rounded-bubble px-4.5 py-2.5 text-sm leading-relaxed break-words whitespace-pre-wrap"
      :class="sender === 'user' ? 'bg-primary text-white' : 'border border-slate-200 bg-white text-slate-700'"
    >
      <slot />
    </p>
  </div>
</template>
