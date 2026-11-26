<template>
  <div>
    <!-- セクションごとに上下の余白を持たせるため、PageContainer の上下の余白は外す -->
    <CommonPageContainer :padded="false" class="pt-16">
      <!-- ===== categories ===== -->
      <section id="categories" class="py-10">
        <CommonSectionTitle size="lg" class="mb-6">カテゴリから探す</CommonSectionTitle>
        <div v-if="categoriesStatus === 'pending' && categories.length === 0" class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <div v-for="n in 6" :key="n" class="h-[126px] animate-pulse border border-slate-200 bg-slate-100" />
        </div>
        <p v-else-if="categoriesError" class="border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
          カテゴリを読み込めませんでした。時間をおいて再度お試しください。
        </p>
        <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <!-- TODO: カテゴリで絞り込んだ商品一覧ページができたら、そこへのリンクにする -->
          <div
            v-for="category in categories"
            :key="category.category_id"
            class="flex cursor-pointer flex-col items-center gap-2.5 border border-slate-200 bg-white px-3 py-7 text-center transition-colors hover:border-primary"
          >
            <svg
              class="text-primary"
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
              v-html="categoryIcon(category.category_id)"
            />
            <h3 class="text-sm font-bold text-slate-900">{{ category.category_name }}</h3>
            <span class="text-xs text-slate-500">{{ category.product_count.toLocaleString('ja-JP') }}点</span>
          </div>
        </div>
      </section>

      <!-- ===== featured listings ===== -->
      <!-- 商品が新着の4件分しか無いときは、注目に出す商品が無いのでセクションごと隠す -->
      <section v-if="showFeatured" class="py-10">
        <div class="mb-5 flex items-baseline justify-between">
          <CommonSectionTitle size="lg">注目のチャットボット</CommonSectionTitle>
          <a href="#" class="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:underline">
            もっと見る
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </a>
        </div>
        <ProductCardGrid :products="featuredProducts" :status="featuredStatus" :error="featuredError" />
      </section>

      <!-- ===== new arrivals ===== -->
      <section class="py-10">
        <div class="mb-5 flex items-baseline justify-between">
          <CommonSectionTitle size="lg">新着出品</CommonSectionTitle>
          <a href="#" class="inline-flex items-center gap-1.5 text-sm font-bold text-primary hover:underline">
            もっと見る
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="9 18 15 12 9 6"></polyline></svg>
          </a>
        </div>
        <ProductCardGrid :products="newProducts" :status="newStatus" :error="newError" />
      </section>
    </CommonPageContainer>

    <!-- ===== CTA ===== -->
    <CommonPageContainer :padded="false" class="my-14">
      <UCard :ui="{ body: 'flex flex-col items-center gap-4 px-8 py-14 text-center sm:px-8 sm:py-14' }">
        <CommonSectionTitle size="lg">あなたのボットも、出品してみませんか？</CommonSectionTitle>
        <p class="mx-auto max-w-[72ch] text-base text-slate-700">
          PDFをアップロードするだけで簡単にチャットボットを作成できます。<br>
          あなたの作成したチャットボットも誰かにとって価値があるかもしれません。
        </p>
        <UButton size="lg">出品をはじめる</UButton>
      </UCard>
    </CommonPageContainer>
  </div>
</template>

<script setup>
useHead({
  title: 'BOTMARKET | チャットボットCtoCマーケット',
})

// 商品・カテゴリはAPIから取得する(3つを並行して取得し、SSRで描画してから返す)
const [
  { data: categories, status: categoriesStatus, error: categoriesError },
  { data: newProducts, status: newStatus, error: newError },
  { data: featuredProducts, status: featuredStatus, error: featuredError },
] = await Promise.all([
  useCategories(),
  useProductList({ limit: 4 }),
  // TODO: 注目の基準(評価・販売数など)が決まるまでは、新着の次の4件を表示する
  useProductList({ limit: 4, offset: 4 }),
])

// 注目は、読み込み中・取得失敗のときは枠を出し、取得できて0件のときだけ隠す
const showFeatured = computed(() => featuredStatus.value !== 'success' || featuredProducts.value.length > 0)
</script>
