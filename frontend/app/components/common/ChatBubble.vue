<!--
  チャットの吹き出し 1 件分（形は「吹き出しピル」：角丸 22px で 1 行ならピル型、発言者側の下の角だけ直角）
  sender="user" … 右寄せ・primary の塗り・右下が直角
  sender="bot"  … 左寄せ・白地に枠線・左下が直角。avatar に 1 文字渡すと左に丸いアイコンを出す
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
  <div class="flex items-end gap-2" :class="sender === 'user' ? 'justify-end' : 'justify-start'">
    <span
      v-if="sender === 'bot' && avatar"
      aria-hidden="true"
      class="flex size-7 flex-none items-center justify-center rounded-full bg-primary-100 text-xs font-bold text-primary-700"
    >
      {{ avatar }}
    </span>
    <p
      class="m-0 max-w-[85%] rounded-bubble px-4.5 py-2.5 text-sm leading-relaxed break-words whitespace-pre-wrap"
      :class="sender === 'user' ? 'rounded-br-none bg-primary text-white' : 'rounded-bl-none border border-slate-200 bg-white text-slate-700'"
    >
      <slot />
    </p>
  </div>
</template>
