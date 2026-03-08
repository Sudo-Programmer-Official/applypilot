<template>
  <footer class="product-footer">
    <div class="product-footer-inner">
      <div class="footer-brand">
        <p class="footer-kicker">ApplyPilot</p>
        <strong>Resume workspace</strong>
        <p>
          Built for focused resume optimization with a cleaner split between marketing, product workflow, and launch
          essentials.
        </p>
      </div>

      <div class="footer-links">
        <div class="footer-column">
          <span class="footer-label">Product</span>
          <RouterLink to="/dashboard">Dashboard</RouterLink>
          <RouterLink to="/dashboard/wizard">Optimize</RouterLink>
          <RouterLink to="/dashboard/history">History</RouterLink>
        </div>

        <div class="footer-column">
          <span class="footer-label">Company</span>
          <RouterLink to="/">Landing</RouterLink>
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
        </div>

        <div class="footer-column">
          <span class="footer-label">Launch</span>
          <span class="status-pill">Guest mode</span>
          <a href="mailto:hello@applypilot.com">hello@applypilot.com</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.product-footer {
  border-top: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(255, 255, 255, 0.7);
}

.product-footer-inner {
  display: flex;
  justify-content: space-between;
  gap: 28px;
  align-items: start;
  max-width: 1360px;
  margin: 0 auto;
  padding: 24px;
}

.footer-brand {
  max-width: 28rem;
}

.footer-kicker,
.footer-label {
  display: block;
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.footer-brand strong {
  display: block;
  font-size: 1rem;
}

.footer-brand p:last-child {
  margin: 10px 0 0;
  color: #5f6c80;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, auto));
  gap: 28px;
}

.footer-column {
  display: grid;
  gap: 10px;
  justify-items: start;
}

.footer-column a {
  color: #4f5e75;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

@media (max-width: 960px) {
  .product-footer-inner {
    flex-direction: column;
    padding: 20px 16px;
  }

  .footer-links {
    width: 100%;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .footer-links {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
