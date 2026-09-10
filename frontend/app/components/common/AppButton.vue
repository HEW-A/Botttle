<template>
  <NuxtLink v-if="to" :to="to" :class="buttonClass">
    <slot />
  </NuxtLink>
  <button v-else :class="buttonClass">
    <slot />
  </button>
</template>

<script setup>
const props = defineProps({
  to: {
    type: String,
    default: null,
  },
  variant: {
    type: String,
    default: 'primary', // 'primary' | 'outline' | 'outline-white'
  },
  size: {
    type: String,
    default: 'sm', // 'sm' | 'lg'
  },
})

const variantClass = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  outline: 'border border-gray-300 hover:bg-gray-100',
  'outline-white': 'border border-white text-white hover:bg-white/10',
}

const sizeClass = {
  sm: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
}

const buttonClass = computed(() => [
  'inline-flex items-center whitespace-nowrap rounded-md font-medium',
  variantClass[props.variant],
  sizeClass[props.size],
])
</script>
