<template>
  <div class="flex min-h-screen flex-col">
    <CommonAppHeader />

    <main class="flex-1">
      <slot />
    </main>

    <CommonAppFooter />
  </div>
</template>
