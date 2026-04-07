import axios from 'axios'

import type {
  PortfolioActivityCreatePayload,
  PortfolioBootstrapPayload,
  PortfolioOverview,
  PortfolioProfile,
  PortfolioProfileUpdatePayload,
  PublicPortfolioOverview,
} from '../types/portfolio'
import { getRequiredAuthHeaders } from './firebaseAuth'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function fetchPortfolioMe() {
  const response = await axios.get<PortfolioOverview>(`${apiBase}/portfolio/me`, {
    headers: await getRequiredAuthHeaders(),
  })
  return response.data
}

export async function fetchPublicPortfolio(username: string) {
  const response = await axios.get<PublicPortfolioOverview>(`${apiBase}/portfolio/public/${username}`)
  return response.data
}

export async function bootstrapPortfolio(payload: PortfolioBootstrapPayload) {
  const response = await axios.post<PortfolioOverview>(`${apiBase}/portfolio/bootstrap`, payload, {
    headers: await getRequiredAuthHeaders(),
  })
  return response.data
}

export async function updatePortfolioProfile(payload: PortfolioProfileUpdatePayload) {
  const response = await axios.patch<PortfolioProfile>(`${apiBase}/portfolio/me`, payload, {
    headers: await getRequiredAuthHeaders(),
  })
  return response.data
}

export async function createPortfolioActivity(payload: PortfolioActivityCreatePayload) {
  const response = await axios.post<{ status: string }>(`${apiBase}/portfolio/activity`, payload, {
    headers: await getRequiredAuthHeaders(),
  })
  return response.data
}
