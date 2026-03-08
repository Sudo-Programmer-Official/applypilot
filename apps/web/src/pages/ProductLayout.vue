<script setup lang="ts">
import { RouterView } from 'vue-router'
import ProductFooter from '../components/layout/ProductFooter.vue'
import ProductNavbar from '../components/layout/ProductNavbar.vue'
</script>

<template>
  <div class="product-shell">
    <ProductNavbar />

    <main class="product-main">
      <RouterView />
    </main>

    <ProductFooter />
  </div>
</template>

<style scoped>
.product-shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  background: #f6f4ef;
}

.product-main {
  min-height: 0;
  padding: 24px;
  overflow: hidden;
}

@media (max-width: 1100px) {
  .product-main {
    min-height: 0;
    padding: 16px;
    overflow: visible;
  }
}
</style>
