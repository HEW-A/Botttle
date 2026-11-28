<template>
  <!--
    scroll-body=false: モーダルなどを開いたとき、スクロールバーの幅だけ body に padding-right を足す補正を止める。
    main.css の scrollbar-gutter: stable でスクロールバーの場所は常に確保しているため、補正すると二重になって画面が横にずれる。
    (背景のスクロールを止める処理自体はそのまま効く)
  -->
  <UApp :scroll-body="false">
    <NuxtRouteAnnouncer />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
