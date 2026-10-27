import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import 'react-datepicker/dist/react-datepicker.css'
import App from './App.tsx'
import { APP_NAME, APP_TAGLINE } from '@/lib/branding'

document.title = `${APP_NAME} — ${APP_TAGLINE}`

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
