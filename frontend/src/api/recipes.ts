import client from './client'
import type { CategoryOut, DiffOut, RecipeContent, RecipeDetailOut, RecipeOut, RecipeVersionDetail, RecipeVersionOut, TagOut } from '@/types'

export const recipesApi = {
  async list(params?: { search?: string; category?: string; tag?: string; page?: number }) {
    const { data } = await client.get<RecipeDetailOut[]>('/recipes/', { params })
    return data
  },
  async listShared(params?: { search?: string; page?: number }) {
    const { data } = await client.get<RecipeDetailOut[]>('/recipes/shared', { params })
    return data
  },
  async get(id: number) {
    const { data } = await client.get<RecipeDetailOut>(`/recipes/${id}`)
    return data
  },
  async create(content: RecipeContent) {
    const { data } = await client.post<RecipeDetailOut>('/recipes/', { content })
    return data
  },
  async updateDraft(id: number, content: RecipeContent) {
    const { data } = await client.patch<RecipeDetailOut>(`/recipes/${id}/draft`, { content })
    return data
  },
  async saveVersion(id: number, content: RecipeContent) {
    const { data } = await client.post(`/recipes/${id}/versions`, { content })
    return data
  },
  async getVersion(id: number, versionNumber: number) {
    const { data } = await client.get<RecipeVersionDetail>(`/recipes/${id}/versions/${versionNumber}`)
    return data
  },
  async rateVersion(id: number, versionNumber: number, rating: number) {
    const { data } = await client.patch<RecipeVersionOut>(`/recipes/${id}/versions/${versionNumber}/rating`, { rating })
    return data
  },
  async getDiff(id: number, v1: number, v2: number) {
    const { data } = await client.get<DiffOut>(`/recipes/${id}/diff`, { params: { v1, v2 } })
    return data
  },
  async updateMeta(id: number, payload: { is_shared?: boolean }) {
    const { data } = await client.patch<RecipeOut>(`/recipes/${id}`, payload)
    return data
  },
  async delete(id: number) {
    await client.delete(`/recipes/${id}`)
  },
  async fork(id: number) {
    const { data } = await client.post<RecipeDetailOut>(`/recipes/${id}/fork`)
    return data
  },
  async getCategories() {
    const { data } = await client.get<CategoryOut[]>('/categories/')
    return data
  },
  async getTags() {
    const { data } = await client.get<TagOut[]>('/tags/')
    return data
  }
}
