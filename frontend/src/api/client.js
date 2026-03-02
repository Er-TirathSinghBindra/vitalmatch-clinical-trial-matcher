import axios from 'axios'

// API Gateway endpoint - update this with your actual endpoint
const API_BASE_URL = import.meta.env.VITE_API_ENDPOINT || 'https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com/prod'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for logging and adding auth if needed
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    
    // Handle specific error cases
    if (error.code === 'ECONNABORTED') {
      return Promise.reject(new Error('Request timeout'))
    }
    
    if (!error.response) {
      return Promise.reject(new Error('Network error'))
    }
    
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        return Promise.reject(new Error(data.message || 'Invalid patient profile'))
      case 404:
        return Promise.reject(new Error('Service not found'))
      case 429:
        return Promise.reject(new Error('Too many requests'))
      case 500:
        return Promise.reject(new Error('Server error'))
      case 503:
        return Promise.reject(new Error('Service temporarily unavailable'))
      default:
        return Promise.reject(new Error(data.message || 'An unexpected error occurred'))
    }
  }
)

/**
 * Match trials based on patient profile
 * @param {Object} patientProfile - Patient profile data
 * @param {string} patientProfile.condition - Medical condition
 * @param {number} patientProfile.age - Patient age
 * @param {string} patientProfile.gender - Patient gender
 * @param {string} patientProfile.location - Patient location
 * @param {number} patientProfile.distance_miles - Search radius in miles
 * @param {string} patientProfile.medical_history - Medical history text
 * @returns {Promise<Object>} Match results
 */
export const matchTrials = async (patientProfile) => {
  try {
    const response = await apiClient.post('/match-trials', {
      patient_profile: patientProfile
    })
    
    return response.data
  } catch (error) {
    // Retry logic for transient failures
    if (error.message && (error.message.includes('Network error') || error.message.includes('Request timeout'))) {
      console.log('Retrying request...')
      try {
        const retryResponse = await apiClient.post('/match-trials', {
          patient_profile: patientProfile
        })
        return retryResponse.data
      } catch (retryError) {
        throw retryError
      }
    }
    
    throw error
  }
}

/**
 * Health check endpoint (if available)
 * @returns {Promise<Object>} Health status
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check failed:', error)
    return { status: 'unavailable' }
  }
}

export default apiClient
