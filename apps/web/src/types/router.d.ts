import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    canonicalPath?: string
    description?: string
    image?: string
    ogType?: string
    robots?: string
    structuredData?: Record<string, unknown> | Array<Record<string, unknown>>
    title?: string
  }
}

export {}
