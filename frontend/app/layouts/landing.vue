<!-- トップページ（LP）用のレイアウト。ヘッダーは常にゲスト表示で、検索・ランキングを出さない。背景は白 -->
<template>
  <div class="flex min-h-screen flex-col bg-white">
    <CommonAppHeader force-guest hide-search hide-ranking />

    <main class="flex-1">
      <slot />
    </main>

    <CommonAppFooter />
  </div>
</template>
