<script setup lang="ts">
import PublicFooter from './PublicFooter.vue'
import PublicNav from './PublicNav.vue'
</script>

<template>
  <div class="public-shell">
    <div class="background-orb orb-left" aria-hidden="true"></div>
    <div class="background-orb orb-right" aria-hidden="true"></div>

    <PublicNav />

    <main class="public-main">
      <slot />
    </main>

    <PublicFooter />
  </div>
</template>

<style scoped>
.public-shell {
  position: relative;
  min-height: 100vh;
  overflow: clip;
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.18), transparent 24%),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 24%),
    linear-gradient(180deg, #fbfaf6 0%, #f4f0e7 100%);
}

.public-main {
  position: relative;
  z-index: 1;
}

.background-orb {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  filter: blur(38px);
  opacity: 0.48;
}

.orb-left {
  top: 140px;
  left: -180px;
  background: rgba(251, 191, 36, 0.26);
}

.orb-right {
  top: 280px;
  right: -160px;
  background: rgba(37, 99, 235, 0.2);
}
</style>
