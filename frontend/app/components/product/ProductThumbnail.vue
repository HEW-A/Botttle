<template>
  <img
    v-if="src && !failed"
    ref="imageEl"
    :src="src"
    :alt="alt"
    :loading="loading"
    class="h-full w-full object-cover"
    @error="failed = true"
  />
  <!-- 画像が無い・読み込めないときの表示 -->
  <slot v-else />
</template>

<script setup lang="ts">
// 商品のサムネイル画像。URLが無いときや、URLの先に画像が無いとき(Storageから消えた場合など)は、
// 壊れた画像のアイコンではなく slot の中身を表示する
const props = withDefaults(
  defineProps<{
    src: string | null | undefined
    alt: string
    loading?: 'lazy' | 'eager'
  }>(),
  { loading: 'lazy' },
)

const failed = ref(false)
const imageEl = ref<HTMLImageElement | null>(null)

// SSRで描画した画像は、ブラウザ側の準備(hydration)が終わる前に読み込みに失敗すると
// @error を受け取れないため、表示した時点でも読み込めているかを確かめる
onMounted(() => {
  const el = imageEl.value
  if (el && el.complete && el.naturalWidth === 0) failed.value = true
})

// 別の商品に切り替わったら、もう一度読み込みを試す
watch(
  () => props.src,
  () => {
    failed.value = false
  },
)
</script>
