import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ta_access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry && localStorage.getItem('ta_refresh_token')) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('ta_refresh_token')
        const { data } = await axios.post('/api/auth/token/refresh/', { refresh })
        localStorage.setItem('ta_access_token', data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.removeItem('ta_access_token')
        localStorage.removeItem('ta_refresh_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
