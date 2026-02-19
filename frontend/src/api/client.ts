import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

// Attach access token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401: attempt a token refresh, then retry the original request
let isRefreshing = false
let failedQueue: { resolve: (t: string) => void; reject: (e: unknown) => void }[] = []

client.interceptors.response.use(
  (r) => r,
  async (error) => {
    const orig = error.config
    if (error.response?.status !== 401 || orig._retry) return Promise.reject(error)

    if (isRefreshing) {
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then((token) => {
        orig.headers.Authorization = `Bearer ${token}`
        return client(orig)
      })
    }

    orig._retry = true
    isRefreshing = true
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) {
      window.location.href = '/login'
      return Promise.reject(error)
    }

    try {
      const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
      localStorage.setItem('access_token', data.access_token)
      failedQueue.forEach(p => p.resolve(data.access_token))
      failedQueue = []
      orig.headers.Authorization = `Bearer ${data.access_token}`
      return client(orig)
    } catch (e) {
      failedQueue.forEach(p => p.reject(e))
      failedQueue = []
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(e)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
