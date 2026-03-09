export const SITE_URL = 'https://tryapplypilot.com'
export const SITE_NAME = 'ApplyPilot'
export const DEFAULT_TITLE = 'ApplyPilot | AI Resume Optimizer and ATS Resume Checker'
export const DEFAULT_DESCRIPTION =
  'Optimize resumes for ATS screening and recruiter review with guided analysis, keyword checks, and AI rewriting.'
export const DEFAULT_IMAGE = `${SITE_URL}/og-image.png`

type StructuredData = Record<string, unknown> | Array<Record<string, unknown>>

type RouteSeoMeta = {
  canonicalPath?: string
  description?: string
  image?: string
  ogType?: string
  robots?: string
  structuredData?: StructuredData
  title?: string
}

const ROUTE_STRUCTURED_DATA_ATTR = 'data-route-structured-data'

function upsertMeta(attribute: 'name' | 'property', value: string, content: string) {
  let meta = document.head.querySelector<HTMLMetaElement>(`meta[${attribute}="${value}"]`)

  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute(attribute, value)
    document.head.append(meta)
  }

  meta.setAttribute('content', content)
}

function upsertLink(rel: string, href: string) {
  let link = document.head.querySelector<HTMLLinkElement>(`link[rel="${rel}"]`)

  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', rel)
    document.head.append(link)
  }

  link.setAttribute('href', href)
}

function clearStructuredData() {
  document.head.querySelectorAll(`[${ROUTE_STRUCTURED_DATA_ATTR}]`).forEach((node) => node.remove())
}

function injectStructuredData(structuredData?: StructuredData) {
  clearStructuredData()

  if (!structuredData) {
    return
  }

  const payloads = Array.isArray(structuredData) ? structuredData : [structuredData]

  payloads.forEach((payload) => {
    const script = document.createElement('script')
    script.type = 'application/ld+json'
    script.setAttribute(ROUTE_STRUCTURED_DATA_ATTR, 'true')
    script.text = JSON.stringify(payload)
    document.head.append(script)
  })
}

export function toAbsoluteUrl(path = '/') {
  return new URL(path, SITE_URL).toString()
}

export function applyRouteSeo(meta: RouteSeoMeta = {}) {
  const title = meta.title ?? DEFAULT_TITLE
  const description = meta.description ?? DEFAULT_DESCRIPTION
  const canonicalUrl = toAbsoluteUrl(meta.canonicalPath ?? '/')
  const image = meta.image ? toAbsoluteUrl(meta.image) : DEFAULT_IMAGE
  const robots = meta.robots ?? 'index,follow'
  const ogType = meta.ogType ?? 'website'

  document.title = title

  upsertMeta('name', 'description', description)
  upsertMeta('name', 'robots', robots)
  upsertMeta('property', 'og:title', title)
  upsertMeta('property', 'og:description', description)
  upsertMeta('property', 'og:url', canonicalUrl)
  upsertMeta('property', 'og:type', ogType)
  upsertMeta('property', 'og:site_name', SITE_NAME)
  upsertMeta('property', 'og:image', image)
  upsertMeta('name', 'twitter:card', 'summary_large_image')
  upsertMeta('name', 'twitter:title', title)
  upsertMeta('name', 'twitter:description', description)
  upsertMeta('name', 'twitter:image', image)
  upsertLink('canonical', canonicalUrl)

  injectStructuredData(meta.structuredData)
}

function buildOrganization() {
  return {
    '@type': 'Organization',
    name: SITE_NAME,
    url: SITE_URL,
    logo: `${SITE_URL}/icons/icon-512x512.png`,
  }
}

export function createWebsiteSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_NAME,
    url: SITE_URL,
    description: DEFAULT_DESCRIPTION,
    publisher: buildOrganization(),
  }
}

export function createSoftwareApplicationSchema(input: {
  description: string
  featureList?: string[]
  name: string
  path: string
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: input.name,
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    url: toAbsoluteUrl(input.path),
    description: input.description,
    featureList: input.featureList,
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
    publisher: buildOrganization(),
  }
}

export function createFaqSchema(items: Array<{ answer: string; question: string }>) {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  }
}

export function createBlogSchema(input: { description: string; path: string; title: string }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: input.title,
    description: input.description,
    url: toAbsoluteUrl(input.path),
    publisher: buildOrganization(),
  }
}

export function createBlogPostingSchema(input: {
  datePublished: string
  description: string
  path: string
  title: string
}) {
  const absoluteUrl = toAbsoluteUrl(input.path)

  return {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: input.title,
    description: input.description,
    url: absoluteUrl,
    mainEntityOfPage: absoluteUrl,
    datePublished: input.datePublished,
    dateModified: input.datePublished,
    author: {
      '@type': 'Organization',
      name: `${SITE_NAME} Team`,
    },
    publisher: buildOrganization(),
    image: DEFAULT_IMAGE,
  }
}
