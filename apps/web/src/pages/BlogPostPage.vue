<script setup lang="ts">
import { computed } from 'vue'
import PublicLayout from '../components/marketing/PublicLayout.vue'
import { blogPostsBySlug } from '../content/blogPosts'
import { seoLandingPagesBySlug, type SeoLandingPageContent } from '../content/seoLandingPages'

const props = defineProps<{
  slug: string
}>()

const post = computed(() => blogPostsBySlug[props.slug])
const relatedTools = computed(() => {
  const content = post.value

  if (!content) {
    return []
  }

  return content.relatedToolSlugs
    .map((slug) => seoLandingPagesBySlug[slug])
    .filter((tool): tool is SeoLandingPageContent => Boolean(tool))
})

const formatter = new Intl.DateTimeFormat('en-US', {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
})
</script>

<template>
  <PublicLayout>
    <article v-if="post" class="post-shell">
      <header class="post-hero">
        <p class="eyebrow">ApplyPilot guide</p>
        <h1>{{ post.title }}</h1>
        <p class="post-summary">{{ post.intro }}</p>

        <div class="post-meta">
          <span>{{ formatter.format(new Date(post.datePublished)) }}</span>
          <span>Resume strategy</span>
        </div>
      </header>

      <section class="section-grid">
        <article v-for="section in post.sections" :key="section.title" class="section-card">
          <h2>{{ section.title }}</h2>
          <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>

          <ul v-if="section.bullets" class="bullet-list">
            <li v-for="bullet in section.bullets" :key="bullet">{{ bullet }}</li>
          </ul>
        </article>
      </section>

      <section v-if="relatedTools.length" class="related-card">
        <div class="section-head">
          <p class="eyebrow">Related pages</p>
          <h2>Turn the advice into a guided workflow</h2>
        </div>

        <div class="related-grid">
          <RouterLink
            v-for="tool in relatedTools"
            :key="tool.slug"
            class="related-link"
            :to="`/${tool.slug}`"
          >
            <strong>{{ tool.navLabel }}</strong>
            <span>{{ tool.metaDescription }}</span>
          </RouterLink>
        </div>
      </section>

      <section class="cta-card">
        <div>
          <p class="eyebrow">Try ApplyPilot</p>
          <h2>{{ post.ctaTitle }}</h2>
          <p>{{ post.ctaDescription }}</p>
        </div>

        <RouterLink class="cta-button" to="/dashboard/wizard">Open the resume workflow</RouterLink>
      </section>
    </article>
  </PublicLayout>
</template>

<style scoped>
.post-shell {
  display: grid;
  gap: 24px;
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.post-hero,
.section-card,
.related-card,
.cta-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 16px 40px rgba(20, 33, 61, 0.08);
}

.post-hero,
.related-card,
.cta-card {
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

.post-hero h1,
.section-card h2,
.section-head h2,
.cta-card h2 {
  margin: 0;
  line-height: 0.98;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.post-hero h1 {
  max-width: 12ch;
  font-size: clamp(2.8rem, 6vw, 4.9rem);
}

.post-summary,
.section-card p,
.section-card li,
.related-link span,
.cta-card p,
.post-meta {
  color: #5f6c80;
}

.post-summary {
  max-width: 42rem;
  margin: 18px 0 0;
  font-size: 1.08rem;
}

.post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
  font-weight: 700;
}

.section-grid,
.related-grid {
  display: grid;
  gap: 18px;
}

.section-card {
  padding: 24px;
}

.bullet-list {
  padding-left: 22px;
}

.related-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.related-link {
  display: grid;
  gap: 10px;
  padding: 20px;
  border-radius: 18px;
  color: inherit;
  background: rgba(20, 33, 61, 0.05);
}

.section-head {
  margin-bottom: 18px;
}

.cta-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 18px;
  border-radius: 999px;
  color: #fff;
  font-weight: 700;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

@media (max-width: 900px) {
  .related-grid {
    grid-template-columns: 1fr;
  }

  .cta-card {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 720px) {
  .post-shell {
    padding: 24px 16px 48px;
  }

  .post-hero,
  .section-card,
  .related-card,
  .cta-card {
    padding: 24px;
  }

  .cta-button {
    width: 100%;
  }
}
</style>
