import { reactive, readonly } from 'vue'

import { initializeApp, getApp, getApps } from 'firebase/app'
import {
  GoogleAuthProvider,
  getAuth,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type Auth,
  type User,
} from 'firebase/auth'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
}

const isFirebaseConfigured = Object.values(firebaseConfig).every(Boolean)

const state = reactive({
  enabled: isFirebaseConfigured,
  ready: !isFirebaseConfigured,
  busy: false,
  user: null as User | null,
  error: '',
})

let authInstance: Auth | null = null
let readyResolver: (() => void) | null = null
const readyPromise = new Promise<void>((resolve) => {
  readyResolver = resolve
})

function resolveReady() {
  if (!state.ready) {
    state.ready = true
    readyResolver?.()
  }
}

function ensureFirebaseAuth() {
  if (!isFirebaseConfigured) {
    resolveReady()
    return null
  }
  if (authInstance) {
    return authInstance
  }

  const app = getApps().length ? getApp() : initializeApp(firebaseConfig)
  authInstance = getAuth(app)
  onAuthStateChanged(
    authInstance,
    (user: User | null) => {
      state.user = user
      state.error = ''
      resolveReady()
    },
    (error: Error) => {
      state.error = error.message || 'Firebase auth failed to initialize.'
      resolveReady()
    },
  )
  return authInstance
}

ensureFirebaseAuth()

export const authState = readonly(state)

export async function waitForAuthReady() {
  ensureFirebaseAuth()
  if (state.ready) {
    return
  }
  await readyPromise
}

export async function signInWithGoogle() {
  const auth = ensureFirebaseAuth()
  if (!auth) {
    throw new Error('Firebase auth is not configured in the frontend environment.')
  }

  state.busy = true
  state.error = ''
  try {
    const provider = new GoogleAuthProvider()
    const result = await signInWithPopup(auth, provider)
    state.user = result.user
    return result.user
  }
  catch (error) {
    state.error = error instanceof Error ? error.message : 'Google sign-in failed.'
    throw error
  }
  finally {
    state.busy = false
  }
}

export async function signOutCurrentUser() {
  const auth = ensureFirebaseAuth()
  if (!auth) {
    return
  }

  state.busy = true
  state.error = ''
  try {
    await signOut(auth)
    state.user = null
  }
  catch (error) {
    state.error = error instanceof Error ? error.message : 'Sign out failed.'
    throw error
  }
  finally {
    state.busy = false
  }
}

export async function getOptionalAuthHeaders() {
  await waitForAuthReady()
  const token = state.user ? await state.user.getIdToken() : ''
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function getRequiredAuthHeaders() {
  const headers = await getOptionalAuthHeaders()
  if (!headers.Authorization) {
    throw new Error('Sign in with Google to access private ApplyPilot data.')
  }
  return headers
}
