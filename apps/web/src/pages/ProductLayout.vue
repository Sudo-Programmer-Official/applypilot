<script setup lang="ts">
import { RouterView } from 'vue-router'
import ProductNavbar from '../components/layout/ProductNavbar.vue'
</script>

<template>
  <div class="product-shell">
    <ProductNavbar />

    <main class="product-main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.product-shell {
  min-height: 100vh;
  background: #f6f4ef;
}

.product-main {
  height: calc(100vh - 80px);
  padding: 24px;
  overflow: hidden;
}

@media (max-width: 1100px) {
  .product-main {
    height: auto;
    min-height: calc(100vh - 80px);
    padding: 16px;
    overflow: visible;
  }
}
</style>
