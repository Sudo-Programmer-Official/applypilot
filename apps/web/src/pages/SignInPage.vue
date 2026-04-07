<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import PublicLayout from '../components/marketing/PublicLayout.vue'
import { authState, signInWithGoogle, waitForAuthReady } from '../lib/firebaseAuth'

const route = useRoute()
const router = useRouter()

const error = ref('')

const redirectPath = computed(() => {
  const rawRedirect = route.query.redirect
  const value = typeof rawRedirect === 'string' ? rawRedirect : '/dashboard'
  if (!value.startsWith('/') || value.startsWith('//') || value.startsWith('/signin')) {
    return '/dashboard'
  }
  return value
})

const destinationLabel = computed(() => {
  if (redirectPath.value.startsWith('/dashboard/portfolio')) {
    return 'portfolio workspace'
  }
  if (redirectPath.value.startsWith('/dashboard/history')) {
    return 'resume history'
  }
  if (redirectPath.value.startsWith('/dashboard/wizard')) {
    return 'resume workspace'
  }
  return 'dashboard'
})

async function finishRedirect() {
  await router.replace(redirectPath.value)
}

async function handleGoogleSignIn() {
  error.value = ''
  try {
    await signInWithGoogle()
    await finishRedirect()
  } catch (unknownError) {
    if (unknownError instanceof Error) {
      error.value = unknownError.message
      return
    }
    error.value = 'Google sign-in failed.'
  }
}

onMounted(async () => {
  await waitForAuthReady()
  if (authState.enabled && authState.user) {
    await finishRedirect()
  }
})

watch(
  () => authState.user,
  (nextUser) => {
    if (nextUser) {
      void finishRedirect()
    }
  },
)
</script>

<template>
  <PublicLayout>
    <main class="signin-shell">
      <section class="signin-card">
        <p class="eyebrow">Workspace access</p>
        <h1 v-if="authState.enabled">Sign in to continue</h1>
        <h1 v-else>Local workspace mode</h1>

        <p class="summary" v-if="authState.enabled">
          Resume history, portfolio projects, and public proof cards now live inside one account-backed workspace.
          Continue with Google to open your {{ destinationLabel }}.
        </p>
        <p class="summary" v-else>
          Firebase auth is not configured in this environment, so the product shell is running in local fallback mode.
          You can continue directly to the dashboard.
        </p>

        <div class="actions">
          <button
            v-if="authState.enabled"
            class="primary-button"
            type="button"
            :disabled="authState.busy || !authState.ready"
            @click="handleGoogleSignIn"
          >
            {{ authState.busy ? 'Signing in…' : 'Continue with Google' }}
          </button>
          <RouterLink v-else class="primary-button link-button" to="/dashboard">
            Open Dashboard
          </RouterLink>

          <RouterLink class="secondary-button" to="/">
            Back to landing
          </RouterLink>
        </div>

        <div v-if="authState.enabled && authState.user" class="status-pill">
          Redirecting to {{ destinationLabel }}…
        </div>
        <div v-else-if="authState.enabled && !authState.ready" class="status-pill">
          Checking your existing session…
        </div>
        <div v-if="error" class="error-card">
          <strong>Sign-in blocked</strong>
          <p>{{ error }}</p>
        </div>
      </section>
    </main>
  </PublicLayout>
</template>

<style scoped>
.signin-shell {
  max-width: 980px;
  margin: 0 auto;
  padding: 56px 24px 72px;
}

.signin-card {
  display: grid;
  gap: 22px;
  padding: 36px;
  border: 1px solid rgba(20, 33, 61, 0.1);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 24px 52px rgba(20, 33, 61, 0.08);
}

.eyebrow {
  margin: 0;
  color: #8b5e34;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: clamp(2.6rem, 6vw, 4.6rem);
  line-height: 0.95;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.summary {
  max-width: 48rem;
  margin: 0;
  color: #4f5e75;
  font-size: 1.04rem;
  line-height: 1.75;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.primary-button,
.secondary-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-height: 50px;
  padding: 14px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.primary-button {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.primary-button:disabled {
  opacity: 0.65;
}

.secondary-button {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.link-button {
  text-decoration: none;
}

.status-pill {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: fit-content;
  padding: 10px 14px;
  border-radius: 999px;
  color: #124084;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

.error-card {
  padding: 16px 18px;
  border: 1px solid rgba(220, 38, 38, 0.18);
  border-radius: 20px;
  color: #991b1b;
  background: rgba(254, 242, 242, 0.9);
}

.error-card p {
  margin: 6px 0 0;
}

@media (max-width: 720px) {
  .signin-shell {
    padding: 32px 16px 48px;
  }

  .signin-card {
    padding: 28px 24px;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary-button,
  .secondary-button {
    width: 100%;
  }
}
</style>
