/**
 * Device composable - Device registration and fingerprinting
 */
import { ref, onMounted } from 'vue'
import { generateDeviceFingerprint } from '../utils/deviceFingerprint'
import { deviceApi } from '../services/api'

export function useDevice() {
  const deviceId = ref(null)
  const isRegistered = ref(false)
  const error = ref(null)

  /**
   * Register device
   */
  const registerDevice = async () => {
    try {
      // Check if already registered
      const storedDeviceId = localStorage.getItem('deviceId')
      if (storedDeviceId) {
        deviceId.value = storedDeviceId
        isRegistered.value = true
        return
      }

      // Generate fingerprint
      const fingerprint = await generateDeviceFingerprint()

      // Register with backend
      const response = await deviceApi.register(fingerprint)
      
      deviceId.value = response.data.device_id
      localStorage.setItem('deviceId', response.data.device_id)
      isRegistered.value = true
    } catch (err) {
      console.error('Device registration failed:', err)
      error.value = 'Gagal mendaftarkan perangkat. Silakan refresh halaman.'
    }
  }

  // Auto-register on mount
  onMounted(() => {
    registerDevice()
  })

  return {
    deviceId,
    isRegistered,
    error,
    registerDevice,
  }
}
