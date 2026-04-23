/**
 * Application configuration
 */

export const config = {
  // API Configuration
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/chatbot-api',
  
  // App Configuration
  appName: 'Satu Data Pertahanan',
  appVersion: '1.0.0',
  
  // Features
  features: {
    darkMode: true,
    chatHistory: true,
    quickQuestions: true,
  },
  
  // UI Configuration
  ui: {
    maxMessageLength: 500,
    messagesPerPage: 50,
    typingDelay: 100,
  },
  
  // Maintenance Mode
  maintenance: {
    enabled: import.meta.env.VITE_MAINTENANCE_MODE === 'true' || false,
    message: import.meta.env.VITE_MAINTENANCE_MESSAGE || 'Sistem sedang dalam pemeliharaan',
    eta: import.meta.env.VITE_MAINTENANCE_ETA || null, // e.g., "2 jam" or "23:00 WIB"
  },
  
  // Error Handling
  errorHandling: {
    showErrorDetails: import.meta.env.VITE_SHOW_ERROR_DETAILS === 'true' || false,
    retryAttempts: 3,
    retryDelay: 1000, // ms
  },
}

export default config
