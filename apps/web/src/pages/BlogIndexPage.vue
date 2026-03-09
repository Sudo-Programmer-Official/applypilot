<script setup lang="ts">
import PublicLayout from '../components/marketing/PublicLayout.vue'
import { blogPosts } from '../content/blogPosts'
import { seoLandingPages } from '../content/seoLandingPages'

const formatter = new Intl.DateTimeFormat('en-US', {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})

const featuredTools = seoLandingPages
</script>

<template>
  <PublicLayout>
    <section class="blog-shell">
      <section class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">ApplyPilot blog</p>
          <h1>Resume guides built around how candidates actually get filtered and hired.</h1>
          <p class="hero-summary">
            Use the content layer to target search intent, then move readers into the product workflow when they are
            ready to fix their resume.
          </p>
        </div>

        <aside class="sidebar-card">
          <p class="eyebrow">Tool pages</p>
          <h2>Public entry points</h2>
          <div class="sidebar-links">
            <RouterLink v-for="page in featuredTools" :key="page.slug" class="sidebar-link" :to="`/${page.slug}`">
              <strong>{{ page.navLabel }}</strong>
              <span>{{ page.metaDescription }}</span>
            </RouterLink>
          </div>
        </aside>
      </section>

      <section class="post-grid">
        <RouterLink v-for="post in blogPosts" :key="post.slug" class="post-card" :to="`/blog/${post.slug}`">
          <p class="eyebrow">{{ formatter.format(new Date(post.datePublished)) }}</p>
          <h2>{{ post.title }}</h2>
          <p>{{ post.excerpt }}</p>
          <span class="read-more">Read guide</span>
        </RouterLink>
      </section>
    </section>
  </PublicLayout>
</template>

<style scoped>
.blog-shell {
  display: grid;
  gap: 24px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.hero-grid,
.sidebar-card,
.post-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 16px 40px rgba(20, 33, 61, 0.08);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 22px;
}

.hero-copy,
.sidebar-card {
  padding: 28px;
}

.eyebrow {
  margin: 0 0 10px;
  color: #8b5e34;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-copy h1,
.sidebar-card h2,
.post-card h2 {
  margin: 0;
  line-height: 0.98;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.hero-copy h1 {
  max-width: 12ch;
  font-size: clamp(3rem, 7vw, 5.2rem);
}

.hero-summary,
.sidebar-link span,
.post-card p {
  color: #5f6c80;
}

.hero-summary {
  max-width: 42rem;
  margin: 18px 0 0;
  font-size: 1.08rem;
}

.sidebar-links,
.post-grid {
  display: grid;
  gap: 16px;
}

.sidebar-link,
.post-card {
  display: grid;
  gap: 10px;
  color: inherit;
}

.sidebar-link {
  padding: 18px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.post-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.post-card {
  padding: 24px;
}

.read-more {
  color: #2563eb;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .hero-grid,
  .post-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .blog-shell {
    padding: 24px 16px 48px;
  }

  .hero-copy,
  .sidebar-card,
  .post-card {
    padding: 24px;
  }
}
</style>
