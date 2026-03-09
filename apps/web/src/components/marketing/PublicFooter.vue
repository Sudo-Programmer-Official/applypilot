<script setup lang="ts">
import { blogPosts } from '../../content/blogPosts'
import { seoLandingPages } from '../../content/seoLandingPages'

const featuredPosts = blogPosts.slice(0, 3)
</script>

<template>
  <footer class="public-footer">
    <div class="public-footer-inner">
      <div class="footer-brand">
        <p class="footer-kicker">ApplyPilot</p>
        <strong>SEO pages + tool workflow</strong>
        <p>
          Public pages explain the search intent. The dashboard handles the upload, analysis, optimization, and export
          workflow.
        </p>
        <a href="mailto:hello@applypilot.com">hello@applypilot.com</a>
      </div>

      <div class="footer-links">
        <div class="footer-column">
          <span class="footer-label">Product</span>
          <RouterLink to="/">Home</RouterLink>
          <RouterLink to="/dashboard/wizard">Try ApplyPilot</RouterLink>
          <RouterLink to="/dashboard">Dashboard</RouterLink>
        </div>

        <div class="footer-column">
          <span class="footer-label">Use Cases</span>
          <RouterLink v-for="page in seoLandingPages" :key="page.slug" :to="`/${page.slug}`">
            {{ page.navLabel }}
          </RouterLink>
        </div>

        <div class="footer-column">
          <span class="footer-label">Guides</span>
          <RouterLink to="/blog">Blog</RouterLink>
          <RouterLink v-for="post in featuredPosts" :key="post.slug" :to="`/blog/${post.slug}`">
            {{ post.title }}
          </RouterLink>
        </div>

        <div class="footer-column">
          <span class="footer-label">Company</span>
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.public-footer {
  border-top: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(255, 255, 255, 0.74);
}

.public-footer-inner {
  display: flex;
  justify-content: space-between;
  gap: 32px;
  align-items: start;
  max-width: 1240px;
  margin: 0 auto;
  padding: 28px 24px 36px;
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
  font-size: 1.02rem;
}

.footer-brand p:last-of-type {
  margin: 10px 0 14px;
  color: #5f6c80;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, auto));
  gap: 28px;
}

.footer-column {
  display: grid;
  gap: 10px;
  justify-items: start;
}

.footer-column a,
.footer-brand a {
  color: #4f5e75;
}

@media (max-width: 1040px) {
  .public-footer-inner {
    flex-direction: column;
    padding: 24px 16px 32px;
  }

  .footer-links {
    width: 100%;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .footer-links {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
