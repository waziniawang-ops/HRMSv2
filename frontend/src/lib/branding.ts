// Per-deployment identity, baked in at build time via Vite env vars (same
// mechanism as VITE_API_URL). The flagship deployment builds with none of these
// set and keeps today's Visionaries values; each tenant's Render static site is
// built by tenant-admin with VITE_ORG_NAME set to the customer's name. The
// Visionaries look itself (orange theme, layout) is the same for every tenant.
export const PLATFORM_NAME = 'Visionaries Ent.'
export const ORG_NAME = import.meta.env.VITE_ORG_NAME || PLATFORM_NAME
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'HRMSv2'
export const APP_TAGLINE = import.meta.env.VITE_APP_TAGLINE || 'Enterprise HR Platform'
export const CURRENT_YEAR = new Date().getFullYear()

// The login page's demo-credentials panel lists every seeded username and the
// shared demo password — fine for the flagship demo, never for a real tenant.
export const SHOW_DEMO_CREDENTIALS = import.meta.env.VITE_SHOW_DEMO_CREDENTIALS !== 'false'
