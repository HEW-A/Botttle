// Nuxt UI のテーマ設定（ルールの詳細は frontend/docs/design.md）
// 角丸は main.css の --ui-radius: 0 で全体を角なしにし、
// ボタン・入力欄だけここで rounded-control（6px）を指定する。
// ※ Nuxt UI 既定の rounded-md と確実に置き換わるよう、
//   tailwind-merge が解釈できる rounded-(--radius-control) の書き方にしている。
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'blue',
      neutral: 'slate',
    },

    button: {
      slots: {
        base: 'rounded-(--radius-control) font-bold disabled:opacity-100 aria-disabled:opacity-100',
      },
      variants: {
        size: {
          // 小：32px（「BCをチャージ」など）
          sm: { base: 'h-8 px-3 py-0 text-xs' },
          // 標準：44px
          md: { base: 'h-11 px-5 py-0 text-sm' },
          // 大：48px（購入などの CTA）
          lg: { base: 'h-12 px-6 py-0 text-base' },
        },
      },
      compoundVariants: [
        {
          color: 'primary',
          variant: 'solid',
          class:
            'hover:bg-primary-700 active:bg-primary-700 disabled:bg-slate-200 aria-disabled:bg-slate-200 disabled:text-slate-400 aria-disabled:text-slate-400',
        },
        {
          color: 'primary',
          variant: 'outline',
          class:
            'bg-white ring-primary hover:bg-primary-50 active:bg-primary-50 disabled:ring-slate-200 aria-disabled:ring-slate-200 disabled:text-slate-400 aria-disabled:text-slate-400',
        },
        {
          color: 'primary',
          variant: 'ghost',
          class: 'hover:bg-primary-50 active:bg-primary-50 disabled:text-slate-400 aria-disabled:text-slate-400',
        },
      ],
    },

    input: {
      slots: {
        base: 'rounded-(--radius-control) text-slate-900',
      },
      variants: {
        size: {
          md: { base: 'h-11 px-3.5 text-sm' },
        },
      },
    },

    card: {
      slots: {
        body: 'p-6 sm:p-6',
        header: 'px-6 py-4 sm:px-6',
        footer: 'px-6 py-4 sm:px-6',
      },
    },
  },
})
