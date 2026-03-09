<script setup lang="ts">
import { computed } from 'vue'
import { blogPostsBySlug, type BlogPostContent } from '../content/blogPosts'
import { seoLandingPagesBySlug } from '../content/seoLandingPages'
import PublicLayout from '../components/marketing/PublicLayout.vue'

const props = defineProps<{
  slug: string
}>()

const page = computed(() => seoLandingPagesBySlug[props.slug])
const relatedPosts = computed(() => {
  const content = page.value

  if (!content) {
    return []
  }

  return content.relatedPosts
    .map((slug) => blogPostsBySlug[slug])
    .filter((post): post is BlogPostContent => Boolean(post))
})
</script>

<template>
  <PublicLayout>
    <article v-if="page" class="seo-page">
      <section class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">{{ page.navLabel }}</p>
          <h1>{{ page.title }}</h1>
          <p class="hero-summary">{{ page.description }}</p>

          <div class="hero-actions">
            <RouterLink class="cta-button" to="/dashboard/wizard">Try ApplyPilot</RouterLink>
            <RouterLink class="ghost-button" to="/blog">Read resume guides</RouterLink>
          </div>
        </div>

        <aside class="proof-card">
          <p class="eyebrow">{{ page.proofLabel }}</p>
          <h2>{{ page.proofValue }}</h2>
          <p class="proof-summary">{{ page.intro }}</p>

          <div class="benefit-list">
            <div v-for="benefit in page.benefits" :key="benefit" class="benefit-card">
              {{ benefit }}
            </div>
          </div>
        </aside>
      </section>

      <section class="content-card">
        <div class="section-head">
          <p class="eyebrow">{{ page.navLabel }}</p>
          <h2>{{ page.checklistTitle }}</h2>
        </div>

        <div class="chip-grid">
          <span v-for="item in page.checklist" :key="item" class="topic-chip">{{ item }}</span>
        </div>
      </section>

      <section class="section-grid">
        <article v-for="section in page.sections" :key="section.title" class="section-card">
          <h2>{{ section.title }}</h2>
          <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
        </article>
      </section>

      <section class="workflow-card">
        <div class="section-head">
          <p class="eyebrow">Workflow</p>
          <h2>How to use {{ page.navLabel.toLowerCase() }} without guesswork</h2>
        </div>

        <div class="workflow-grid">
          <article v-for="(step, index) in page.workflowSteps" :key="step.title" class="workflow-step">
            <span>{{ index + 1 }}</span>
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
          </article>
        </div>
      </section>

      <section class="faq-grid">
        <article v-for="item in page.faq" :key="item.question" class="faq-card">
          <h2>{{ item.question }}</h2>
          <p>{{ item.answer }}</p>
        </article>
      </section>

      <section v-if="relatedPosts.length" class="related-card">
        <div class="section-head">
          <p class="eyebrow">Related guides</p>
          <h2>Keep building the search and resume workflow</h2>
        </div>

        <div class="related-grid">
          <RouterLink v-for="post in relatedPosts" :key="post.slug" class="related-link" :to="`/blog/${post.slug}`">
            <strong>{{ post.title }}</strong>
            <span>{{ post.excerpt }}</span>
          </RouterLink>
        </div>
      </section>

      <section class="cta-card">
        <div>
          <p class="eyebrow">Try the tool</p>
          <h2>{{ page.ctaTitle }}</h2>
          <p>{{ page.ctaDescription }}</p>
        </div>

        <RouterLink class="cta-button" to="/dashboard/wizard">Open the resume workflow</RouterLink>
      </section>
    </article>
  </PublicLayout>
</template>

<style scoped>
.seo-page {
  display: grid;
  gap: 24px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.hero-grid,
.content-card,
.section-card,
.workflow-card,
.faq-card,
.related-card,
.cta-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 16px 40px rgba(20, 33, 61, 0.08);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.12fr 0.88fr;
  gap: 22px;
}

.hero-copy,
.proof-card,
.content-card,
.workflow-card,
.related-card,
.cta-card {
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
.proof-card h2,
.section-head h2,
.section-card h2,
.cta-card h2,
.faq-card h2 {
  margin: 0;
  line-height: 0.98;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.hero-copy h1 {
  max-width: 12ch;
  font-size: clamp(3rem, 7vw, 5.4rem);
}

.hero-summary,
.proof-summary,
.section-card p,
.workflow-step p,
.faq-card p,
.related-link span,
.cta-card p {
  color: #5f6c80;
}

.hero-summary {
  max-width: 44rem;
  margin: 18px 0 0;
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
  align-items: center;
  justify-content: center;
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

.proof-card {
  display: grid;
  gap: 18px;
}

.proof-card h2 {
  font-size: clamp(1.9rem, 3vw, 2.7rem);
}

.benefit-list {
  display: grid;
  gap: 12px;
}

.benefit-card,
.topic-chip {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.section-head {
  margin-bottom: 18px;
}

.chip-grid,
.section-grid,
.workflow-grid,
.faq-grid,
.related-grid {
  display: grid;
  gap: 16px;
}

.chip-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-card,
.faq-card {
  padding: 24px;
}

.workflow-grid,
.faq-grid,
.related-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.workflow-step {
  padding: 22px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.workflow-step span {
  display: inline-grid;
  place-items: center;
  width: 40px;
  height: 40px;
  margin-bottom: 14px;
  border-radius: 50%;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #b45309, #2563eb);
}

.workflow-step h3,
.related-link strong {
  font-size: 1.08rem;
}

.faq-card h2 {
  font-size: 1.4rem;
}

.related-link {
  display: grid;
  gap: 10px;
  padding: 20px;
  border-radius: 18px;
  color: inherit;
  background: rgba(20, 33, 61, 0.05);
}

.cta-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

@media (max-width: 1100px) {
  .hero-grid,
  .section-grid,
  .workflow-grid,
  .faq-grid,
  .related-grid,
  .chip-grid {
    grid-template-columns: 1fr;
  }

  .cta-card {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 720px) {
  .seo-page {
    padding: 24px 16px 48px;
  }

  .hero-copy,
  .proof-card,
  .content-card,
  .workflow-card,
  .related-card,
  .cta-card,
  .section-card,
  .faq-card {
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
