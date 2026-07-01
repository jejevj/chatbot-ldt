/**
 * Auth Service — panggil POST /v2/admin/login
 */
import { config } from '../config'

const BASE = config.apiBaseUrl  // contoh: https://apps.syscloud.my.id/chatbot-api

export async function loginAdmin(username_user, password_user) {
  const res = await fetch(`${BASE}/v2/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username_user, password_user }),
  })

  const data = await res.json()

  if (!res.ok) {
    throw new Error(data.detail || 'Login gagal')
  }

  return data  // { token, token_type, expires_in, user }
}
