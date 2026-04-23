/**
 * Generate device fingerprint berdasarkan browser & device characteristics
 * Fingerprint ini akan konsisten untuk device yang sama
 */
export async function generateDeviceFingerprint() {
  const components = []

  // 1. Screen resolution
  components.push(`screen:${screen.width}x${screen.height}x${screen.colorDepth}`)

  // 2. Timezone
  components.push(`tz:${Intl.DateTimeFormat().resolvedOptions().timeZone}`)

  // 3. Language
  components.push(`lang:${navigator.language}`)

  // 4. Platform
  components.push(`platform:${navigator.platform}`)

  // 5. User Agent
  components.push(`ua:${navigator.userAgent}`)

  // 6. Hardware concurrency (CPU cores)
  components.push(`cores:${navigator.hardwareConcurrency || 'unknown'}`)

  // 7. Device memory (if available)
  if (navigator.deviceMemory) {
    components.push(`mem:${navigator.deviceMemory}`)
  }

  // 8. Canvas fingerprint
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial'
    ctx.fillText('Device Fingerprint', 2, 2)
    const canvasData = canvas.toDataURL()
    components.push(`canvas:${await hashString(canvasData)}`)
  } catch (e) {
    components.push('canvas:error')
  }

  // 9. WebGL fingerprint
  try {
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
      if (debugInfo) {
        const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
        const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
        components.push(`webgl:${vendor}|${renderer}`)
      }
    }
  } catch (e) {
    components.push('webgl:error')
  }

  // Combine all components
  const fingerprint = components.join('|')
  
  // Hash the fingerprint untuk privacy
  return await hashString(fingerprint)
}

/**
 * Hash string menggunakan SHA-256
 */
async function hashString(str) {
  const encoder = new TextEncoder()
  const data = encoder.encode(str)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  return hashHex
}

/**
 * Get atau generate device ID
 * Device ID disimpan di localStorage dan di-sync dengan server
 */
export async function getDeviceId() {
  // Cek localStorage
  let deviceId = localStorage.getItem('device_id')
  
  if (deviceId) {
    return deviceId
  }

  // Generate fingerprint
  const fingerprint = await generateDeviceFingerprint()
  
  // Register ke server
  try {
    const response = await fetch('/api/device/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        device_fingerprint: fingerprint,
      }),
    })

    if (!response.ok) {
      throw new Error('Failed to register device')
    }

    const data = await response.json()
    deviceId = data.device_id

    // Simpan di localStorage
    localStorage.setItem('device_id', deviceId)
    localStorage.setItem('device_fingerprint', fingerprint)

    return deviceId
  } catch (error) {
    console.error('Error registering device:', error)
    
    // Fallback: generate random device ID
    deviceId = `device-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem('device_id', deviceId)
    
    return deviceId
  }
}

/**
 * Clear device data (untuk testing atau logout)
 */
export function clearDeviceData() {
  localStorage.removeItem('device_id')
  localStorage.removeItem('device_fingerprint')
}
