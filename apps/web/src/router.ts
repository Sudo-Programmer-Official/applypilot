import { createRouter, createWebHistory } from 'vue-router'
import { blogPosts } from './content/blogPosts'
import { seoLandingPages } from './content/seoLandingPages'
import {
  applyRouteSeo,
  createBlogPostingSchema,
  createBlogSchema,
  createFaqSchema,
  createSoftwareApplicationSchema,
  createWebsiteSchema,
  DEFAULT_DESCRIPTION,
} from './lib/seo'
import BlogIndexPage from './pages/BlogIndexPage.vue'
import BlogPostPage from './pages/BlogPostPage.vue'
import DashboardPage from './pages/Dashboard.vue'
import DashboardHomePage from './pages/DashboardHome.vue'
import HistoryPage from './pages/HistoryPage.vue'
import LandingPage from './pages/LandingPage.vue'
import PrivacyPage from './pages/PrivacyPage.vue'
import ProductLayout from './pages/ProductLayout.vue'
import SeoLandingPage from './pages/SeoLandingPage.vue'
import TermsPage from './pages/TermsPage.vue'

const publicToolRoutes = seoLandingPages.map((page) => ({
  path: `/${page.slug}`,
  name: page.slug,
  component: SeoLandingPage,
  props: {
    slug: page.slug,
  },
  meta: {
    title: page.metaTitle,
    description: page.metaDescription,
    canonicalPath: `/${page.slug}`,
    structuredData: [
      createSoftwareApplicationSchema({
        name: page.navLabel,
        description: page.metaDescription,
        path: `/${page.slug}`,
        featureList: page.benefits,
      }),
      createFaqSchema(page.faq),
    ],
  },
}))

const blogPostRoutes = blogPosts.map((post) => ({
  path: `/blog/${post.slug}`,
  name: `blog-${post.slug}`,
  component: BlogPostPage,
  props: {
    slug: post.slug,
  },
  meta: {
    title: post.metaTitle,
    description: post.metaDescription,
    canonicalPath: `/blog/${post.slug}`,
    ogType: 'article',
    structuredData: createBlogPostingSchema({
      title: post.title,
      description: post.metaDescription,
      path: `/blog/${post.slug}`,
      datePublished: post.datePublished,
    }),
  },
}))

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior() {
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingPage,
      meta: {
        title: 'ApplyPilot | AI Resume Optimizer and ATS Resume Checker',
        description: DEFAULT_DESCRIPTION,
        canonicalPath: '/',
        structuredData: [
          createWebsiteSchema(),
          createSoftwareApplicationSchema({
            name: 'ApplyPilot Resume Optimizer',
            description: DEFAULT_DESCRIPTION,
            path: '/',
            featureList: ['ATS resume checker', 'AI resume builder', 'Role-targeted resume optimization'],
          }),
        ],
      },
    },
    ...publicToolRoutes,
    {
      path: '/blog',
      name: 'blog',
      component: BlogIndexPage,
      meta: {
        title: 'ApplyPilot Blog | Resume, ATS, and Job Search Guides',
        description:
          'Read resume, ATS, and job search guides that support ApplyPilot landing pages and convert search traffic into product workflow visits.',
        canonicalPath: '/blog',
        structuredData: createBlogSchema({
          title: 'ApplyPilot Blog',
          description: 'Resume, ATS, and job search guides from ApplyPilot.',
          path: '/blog',
        }),
      },
    },
    ...blogPostRoutes,
    {
      path: '/dashboard',
      component: ProductLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardHomePage,
          meta: {
            title: 'Dashboard | ApplyPilot',
            description: 'Open the ApplyPilot resume workspace.',
            canonicalPath: '/dashboard',
            robots: 'noindex, nofollow',
          },
        },
        {
          path: 'wizard',
          name: 'dashboard-wizard',
          component: DashboardPage,
          meta: {
            title: 'Optimize Resume | ApplyPilot',
            description: 'Upload, analyze, optimize, and export a stronger resume inside ApplyPilot.',
            canonicalPath: '/dashboard/wizard',
            robots: 'noindex, nofollow',
          },
        },
        {
          path: 'history',
          name: 'dashboard-history',
          component: HistoryPage,
          meta: {
            title: 'Resume History | ApplyPilot',
            description: 'Review prior ApplyPilot resume optimization sessions.',
            canonicalPath: '/dashboard/history',
            robots: 'noindex, nofollow',
          },
        },
      ],
    },
    {
      path: '/wizard',
      redirect: '/dashboard/wizard',
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PrivacyPage,
      meta: {
        title: 'Privacy Policy | ApplyPilot',
        description: 'Read the ApplyPilot privacy policy.',
        canonicalPath: '/privacy',
      },
    },
    {
      path: '/terms',
      name: 'terms',
      component: TermsPage,
      meta: {
        title: 'Terms of Service | ApplyPilot',
        description: 'Read the ApplyPilot terms of service.',
        canonicalPath: '/terms',
      },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.afterEach((to) => {
  applyRouteSeo(to.meta)
})

export default router
