<script setup lang="ts">
import PublicLayout from '../components/marketing/PublicLayout.vue'
import { blogPosts } from '../content/blogPosts'
import { seoLandingPages } from '../content/seoLandingPages'

const featureCards = [
  {
    title: 'Guided workflow',
    description: 'Move from upload to export with clear checkpoints instead of one noisy editor.',
  },
  {
    title: 'ATS analysis',
    description: 'Review keyword coverage, weak structure, and missing role signal before rewriting.',
  },
  {
    title: 'AI rewriting',
    description: 'Turn vague bullets into tighter accomplishment statements without losing accuracy.',
  },
]

const workflowSteps = ['Upload', 'Target role', 'Optimize', 'Export']
const featuredPosts = blogPosts.slice(0, 3)
</script>

<template>
  <PublicLayout>
    <main class="landing-shell">
      <section class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">SEO content + resume workflow</p>
          <h1>Make every resume ATS-ready and recruiter-readable.</h1>
          <p class="hero-summary">
            ApplyPilot combines public landing pages that answer search intent with a guided product workflow that
            helps candidates analyze, optimize, and export stronger resumes faster.
          </p>

          <div class="hero-actions">
            <RouterLink class="cta-button" to="/dashboard/wizard">Try it free</RouterLink>
            <RouterLink class="ghost-button" to="/blog">Read the blog</RouterLink>
          </div>
        </div>

        <article class="hero-card">
          <div class="hero-card-top">
            <div>
              <p class="eyebrow">Growth loop</p>
              <h2>Search intent brings readers. The workflow turns them into users.</h2>
            </div>
            <span class="hero-pill">Public pages live</span>
          </div>

          <div class="workflow-rail">
            <div v-for="step in workflowSteps" :key="step" class="workflow-chip">
              <strong>{{ step }}</strong>
              <span>inside one conversion path</span>
            </div>
          </div>
        </article>
      </section>

      <section class="content-section">
        <div class="section-head">
          <p class="eyebrow">Product value</p>
          <h2>Built to improve clarity, alignment, and iteration speed</h2>
        </div>

        <div class="feature-grid">
          <article v-for="feature in featureCards" :key="feature.title" class="feature-card">
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </article>
        </div>
      </section>

      <section class="content-section">
        <div class="section-head">
          <p class="eyebrow">Intent pages</p>
          <h2>Dedicated SEO routes for the searches that already exist</h2>
        </div>

        <div class="intent-grid">
          <RouterLink v-for="page in seoLandingPages" :key="page.slug" class="intent-card" :to="`/${page.slug}`">
            <p class="eyebrow">{{ page.navLabel }}</p>
            <h3>{{ page.title }}</h3>
            <p>{{ page.metaDescription }}</p>
          </RouterLink>
        </div>
      </section>

      <section class="content-section">
        <div class="section-head">
          <p class="eyebrow">Blog content</p>
          <h2>Articles that answer the search before the user opens the tool</h2>
        </div>

        <div class="article-grid">
          <RouterLink v-for="post in featuredPosts" :key="post.slug" class="article-card" :to="`/blog/${post.slug}`">
            <p class="eyebrow">Guide</p>
            <h3>{{ post.title }}</h3>
            <p>{{ post.excerpt }}</p>
            <span>Read article</span>
          </RouterLink>
        </div>
      </section>
    </main>
  </PublicLayout>
</template>

<style scoped>
.landing-shell {
  display: grid;
  gap: 24px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.hero-grid,
.feature-card,
.hero-card,
.intent-card,
.article-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 16px 40px rgba(20, 33, 61, 0.08);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 22px;
}

.hero-copy,
.hero-card {
  padding: 30px;
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
.hero-card h2,
.section-head h2 {
  margin: 0;
  line-height: 0.96;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.hero-copy h1 {
  max-width: 11ch;
  font-size: clamp(3rem, 7vw, 5.6rem);
}

.hero-summary {
  max-width: 42rem;
  margin: 16px 0 0;
  color: #5f6c80;
  font-size: 1.08rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 24px;
}

.cta-button,
.ghost-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 14px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.cta-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.ghost-button {
  color: #14213d;
  background: rgba(20, 33, 61, 0.06);
}

.hero-card-top {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: start;
}

.hero-pill {
  padding: 8px 12px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.84rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

.hero-card h2 {
  font-size: clamp(1.8rem, 3vw, 2.4rem);
}

.workflow-rail {
  display: grid;
  gap: 12px;
  margin-top: 22px;
}

.workflow-chip {
  padding: 18px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.workflow-chip strong,
.workflow-chip span {
  display: block;
}

.workflow-chip span,
.feature-card p,
.intent-card p,
.article-card p {
  color: #5f6c80;
}

.content-section {
  display: grid;
  gap: 18px;
}

.feature-grid,
.intent-grid,
.article-grid {
  display: grid;
  gap: 18px;
}

.feature-grid,
.intent-grid,
.article-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.feature-card,
.intent-card,
.article-card {
  padding: 24px;
  color: inherit;
}

.feature-card h3,
.intent-card h3,
.article-card h3 {
  margin: 0;
  font-size: 1.24rem;
}

.article-card span {
  color: #2563eb;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .hero-grid,
  .feature-grid,
  .intent-grid,
  .article-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .landing-shell {
    padding: 24px 16px 48px;
  }

  .hero-copy,
  .hero-card,
  .feature-card,
  .intent-card,
  .article-card {
    padding: 24px;
  }

  .hero-actions {
    flex-direction: column;
  }

  .cta-button,
  .ghost-button {
    width: 100%;
  }
}
</style>
