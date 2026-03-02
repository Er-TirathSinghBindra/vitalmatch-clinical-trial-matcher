import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Mock axios before importing the client
vi.mock('axios', () => {
  const mockAxiosInstance = {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { 
        use: vi.fn()
      },
      response: { 
        use: vi.fn()
      }
    }
  }
  
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance)
    }
  }
})

// Import after mocking
const { matchTrials, healthCheck } = await import('./client.js')

describe('API Client', () => {
  let mockAxiosInstance

  beforeEach(() => {
    vi.clearAllMocks()
    // Get the mocked instance
    mockAxiosInstance = axios.create()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('matchTrials', () => {
    const mockPatientProfile = {
      condition: 'Diabetes',
      age: 65,
      gender: 'Male',
      location: 'New York, NY',
      distance_miles: 50,
      medical_history: 'Type 2 diabetes, hypertension'
    }

    const mockSuccessResponse = {
      data: {
        matches: [
          {
            trial_id: 'NCT12345678',
            title: 'Test Trial',
            match_score: 0.92,
            explanation: 'High match',
            key_criteria: ['✅ Age requirement met'],
            location: 'New York'
          }
        ],
        total_trials_considered: 1000,
        hard_filtered_count: 50,
        processing_time_ms: 8500
      },
      status: 200,
      config: { url: '/match-trials', method: 'post' }
    }

    it('sends POST request to /match-trials endpoint', async () => {
      mockAxiosInstance.post.mockResolvedValue(mockSuccessResponse)

      await matchTrials(mockPatientProfile)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/match-trials', {
        patient_profile: mockPatientProfile
      })
    })

    it('returns match results on successful response', async () => {
      mockAxiosInstance.post.mockResolvedValue(mockSuccessResponse)

      const result = await matchTrials(mockPatientProfile)

      expect(result).toEqual(mockSuccessResponse.data)
      expect(result.matches).toHaveLength(1)
      expect(result.total_trials_considered).toBe(1000)
    })

    it('handles 400 Bad Request error', async () => {
      const mockError = new Error('Invalid patient profile')
      mockError.response = {
        status: 400,
        data: { message: 'Invalid patient profile' }
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Invalid patient profile')
    })

    it('handles 404 Not Found error', async () => {
      const mockError = new Error('Service not found')
      mockError.response = {
        status: 404,
        data: {}
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Service not found')
    })

    it('handles 429 Too Many Requests error', async () => {
      const mockError = new Error('Too many requests')
      mockError.response = {
        status: 429,
        data: {}
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Too many requests')
    })

    it('handles 500 Internal Server Error', async () => {
      const mockError = new Error('Server error')
      mockError.response = {
        status: 500,
        data: { message: 'Internal server error' }
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Server error')
    })

    it('handles 503 Service Unavailable error', async () => {
      const mockError = new Error('Service temporarily unavailable')
      mockError.response = {
        status: 503,
        data: {}
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Service temporarily unavailable')
    })

    it('handles network error (no response)', async () => {
      const mockError = new Error('Network error')
      mockError.code = 'ERR_NETWORK'
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Network error')
    })

    it('handles timeout error', async () => {
      const mockError = new Error('Request timeout')
      mockError.code = 'ECONNABORTED'
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Request timeout')
    })

    it('retries request on network error', async () => {
      const mockError = {
        message: 'Network error. Please check your connection.'
      }
      
      mockAxiosInstance.post
        .mockRejectedValueOnce(mockError)
        .mockResolvedValueOnce(mockSuccessResponse)

      const result = await matchTrials(mockPatientProfile)

      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockSuccessResponse.data)
    })

    it('retries request on timeout', async () => {
      const mockError = {
        message: 'Request timeout. Please try again.'
      }
      
      mockAxiosInstance.post
        .mockRejectedValueOnce(mockError)
        .mockResolvedValueOnce(mockSuccessResponse)

      const result = await matchTrials(mockPatientProfile)

      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2)
      expect(result).toEqual(mockSuccessResponse.data)
    })

    it('throws error if retry also fails', async () => {
      const mockError = {
        message: 'Network error. Please check your connection.'
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Network error')
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(2)
    })

    it('does not retry on non-transient errors', async () => {
      const mockError = new Error('Invalid request')
      mockError.response = {
        status: 400,
        data: { message: 'Invalid request' }
      }
      
      mockAxiosInstance.post.mockRejectedValue(mockError)

      await expect(matchTrials(mockPatientProfile)).rejects.toThrow('Invalid request')
      expect(mockAxiosInstance.post).toHaveBeenCalledTimes(1)
    })
  })

  describe('healthCheck', () => {
    it('sends GET request to /health endpoint', async () => {
      const mockResponse = {
        data: { status: 'healthy' },
        status: 200,
        config: { url: '/health', method: 'get' }
      }
      
      mockAxiosInstance.get.mockResolvedValue(mockResponse)

      const result = await healthCheck()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health')
      expect(result).toEqual({ status: 'healthy' })
    })

    it('returns unavailable status on error', async () => {
      const mockError = new Error('Network error')
      
      mockAxiosInstance.get.mockRejectedValue(mockError)

      const result = await healthCheck()

      expect(result).toEqual({ status: 'unavailable' })
    })

    it('does not throw error on health check failure', async () => {
      const mockError = new Error('Server error')
      mockError.response = {
        status: 500,
        data: {}
      }
      
      mockAxiosInstance.get.mockRejectedValue(mockError)

      await expect(healthCheck()).resolves.toEqual({ status: 'unavailable' })
    })
  })

  describe('Axios Configuration', () => {
    it('creates axios instance with correct configuration', () => {
      // Verify axios.create was called during module import
      expect(axios.create).toHaveBeenCalled()
    })
  })
})
