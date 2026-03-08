import { createRouter, createWebHistory } from 'vue-router'
import DashboardPage from './pages/Dashboard.vue'
import DashboardHomePage from './pages/DashboardHome.vue'
import HistoryPage from './pages/HistoryPage.vue'
import LandingPage from './pages/LandingPage.vue'
import PrivacyPage from './pages/PrivacyPage.vue'
import ProductLayout from './pages/ProductLayout.vue'
import TermsPage from './pages/TermsPage.vue'

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
        title: 'ApplyPilot | Resume Copilot',
      },
    },
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
          },
        },
        {
          path: 'wizard',
          name: 'dashboard-wizard',
          component: DashboardPage,
          meta: {
            title: 'Optimize Resume | ApplyPilot',
          },
        },
        {
          path: 'history',
          name: 'dashboard-history',
          component: HistoryPage,
          meta: {
            title: 'Resume History | ApplyPilot',
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
      },
    },
    {
      path: '/terms',
      name: 'terms',
      component: TermsPage,
      meta: {
        title: 'Terms of Service | ApplyPilot',
      },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.afterEach((to) => {
  document.title = (to.meta.title as string) || 'ApplyPilot | Resume Copilot'
})

export default router
