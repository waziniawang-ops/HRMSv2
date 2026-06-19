import axios from 'axios'

export const portalApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

portalApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

portalApi.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('portal_refresh')
      if (refresh) {
        try {
          const apiBase = import.meta.env.VITE_API_URL || '/api/v1'
          const { data } = await axios.post(`${apiBase}/auth/token/refresh/`, { refresh })
          localStorage.setItem('portal_access', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return portalApi(original)
        } catch {
          localStorage.removeItem('portal_access')
          localStorage.removeItem('portal_refresh')
          window.location.href = '/portal/login'
        }
      } else {
        window.location.href = '/portal/login'
      }
    }
    return Promise.reject(err)
  }
)

export default portalApi
