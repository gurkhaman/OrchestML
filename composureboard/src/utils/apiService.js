/**
 * API Service for ComposureCI Orchestrator
 * 
 * Handles communication with the backend composition pipeline
 */

// API Configuration
const API_CONFIG = {
  BASE_URL: 'http://localhost:8000', // Orchestrator service
  ENDPOINTS: {
    COMPOSE: '/api/v1/compose',
    HEALTH: '/api/v1/health'
  },
  TIMEOUT: 60000, // 60 seconds for composition generation
};

/**
 * API Error class for better error handling
 */
export class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Makes a request to the orchestrator API
 * @param {string} endpoint - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} API response
 */
const makeRequest = async (endpoint, options = {}) => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
    timeout: API_CONFIG.TIMEOUT,
  };
  
  const requestOptions = { ...defaultOptions, ...options };
  
  try {
    const response = await fetch(url, requestOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIError(
        `API request failed: ${response.status} ${response.statusText}`,
        response.status,
        errorData
      );
    }
    
    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    
    // Handle network or other errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new APIError(
        'Unable to connect to ComposureCI service. Please check if the orchestrator is running.',
        0,
        { originalError: error.message }
      );
    }
    
    throw new APIError(
      `Request failed: ${error.message}`,
      0,
      { originalError: error.message }
    );
  }
};

/**
 * Submit requirements for composition generation
 * @param {string} requirements - Text requirements from uploaded file
 * @param {Object} constraints - Optional constraints
 * @returns {Promise<Object>} Composition response
 */
export const submitComposition = async (requirements, constraints = {}) => {
  if (!requirements || requirements.trim().length === 0) {
    throw new APIError('Requirements cannot be empty', 400);
  }
  
  const payload = {
    requirements: requirements.trim(),
    constraints
  };
  
  console.log('Submitting composition request:', { 
    requirementsLength: payload.requirements.length,
    constraints 
  });
  
  const response = await makeRequest(API_CONFIG.ENDPOINTS.COMPOSE, {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  
  console.log('Composition response received:', {
    compositionId: response.composition_id,
    status: response.status,
    alternativesCount: response.blueprints?.alternatives?.length || 0
  });
  
  return response;
};

/**
 * Check orchestrator service health
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await makeRequest(API_CONFIG.ENDPOINTS.HEALTH);
    return { status: 'healthy', data: response };
  } catch (error) {
    return { 
      status: 'unhealthy', 
      error: error.message,
      data: error.data 
    };
  }
};

/**
 * Converts API response to mock data format for compatibility
 * @param {Object} apiResponse - Response from /api/v1/compose
 * @returns {Object} Mock data format
 */
export const convertApiResponseToMockFormat = (apiResponse) => {
  if (!apiResponse.blueprints?.alternatives) {
    throw new APIError('Invalid API response format', 500);
  }
  
  return {
    alternatives: apiResponse.blueprints.alternatives,
    metadata: {
      compositionId: apiResponse.composition_id,
      status: apiResponse.status,
      createdAt: apiResponse.created_at
    }
  };
};

/**
 * Test function to validate API connection
 * @returns {Promise<boolean>} True if API is accessible
 */
export const testConnection = async () => {
  try {
    const health = await checkHealth();
    return health.status === 'healthy';
  } catch (error) {
    console.error('API connection test failed:', error.message);
    return false;
  }
};