import client from './client'
import type { SyncResult, UserPublic } from '@/types'

export const authApi = {
  async register(username: string, email: string, password: string) {
    const { data } = await client.post('/auth/register', { username, email, password })
    return data as { access_token: string; refresh_token: string }
  },
  async login(username: string, password: string) {
    const { data } = await client.post('/auth/login', { username, password })
    return data as { access_token: string; refresh_token: string }
  },
  async getMe() {
    const { data } = await client.get('/users/me')
    return data as UserPublic
  },
  async updateMe(payload: {
    email?: string
    github_token?: string
    github_repo_url?: string
    tweak_percentage?: number
  }) {
    const { data } = await client.patch('/users/me', payload)
    return data as UserPublic
  },
  async syncGitHub() {
    const { data } = await client.post<SyncResult>('/sync/')
    return data
  }
}
