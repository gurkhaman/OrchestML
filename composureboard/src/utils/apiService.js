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
    CONFIRM: '/api/v1/compositions/{id}/confirm',
    RECOMPOSE: '/api/v1/recompose',
    STATUS: '/api/v1/compositions/{id}/status',
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
 * Confirm a composition for deployment
 * @param {string} compositionId - UUID of the composition to confirm
 * @param {Object} confirmationData - Deployment context and configuration
 * @returns {Promise<Object>} Confirmation response
 */
export const confirmComposition = async (compositionId, confirmationData) => {
  if (!compositionId || !confirmationData) {
    throw new APIError('Composition ID and confirmation data are required', 400);
  }

  const endpoint = API_CONFIG.ENDPOINTS.CONFIRM.replace('{id}', compositionId);
  
  const payload = {
    confirmed_blueprint: confirmationData.blueprint,
    deployment_context: confirmationData.deploymentContext,
    original_requirements: confirmationData.originalRequirements,
    selected_alternative: confirmationData.selectedAlternativeIndex,
    confirmed_at: new Date().toISOString()
  };

  console.log('Confirming composition:', { 
    compositionId, 
    deploymentContext: confirmationData.deploymentContext 
  });

  const response = await makeRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  console.log('Composition confirmed:', {
    compositionId: response.composition_id,
    status: response.status
  });

  return response;
};

/**
 * Get composition deployment status
 * @param {string} compositionId - UUID of the composition
 * @returns {Promise<Object>} Status response
 */
export const getCompositionStatus = async (compositionId) => {
  if (!compositionId) {
    throw new APIError('Composition ID is required', 400);
  }

  const endpoint = API_CONFIG.ENDPOINTS.STATUS.replace('{id}', compositionId);
  
  try {
    const response = await makeRequest(endpoint);
    return response;
  } catch (error) {
    if (error.status === 404) {
      return { status: 'not_found', message: 'Composition not found' };
    }
    throw error;
  }
};

/**
 * Trigger recomposition for a failed deployment
 * @param {Object} recompositionData - Full recomposition trigger data
 * @returns {Promise<Object>} Recomposition response
 */
export const triggerRecomposition = async (recompositionData) => {
  if (!recompositionData || !recompositionData.composition_id) {
    throw new APIError('Recomposition data with composition_id is required', 400);
  }

  const payload = {
    composition_id: recompositionData.composition_id,
    trigger_type: recompositionData.trigger_type || 'performance_degradation',
    failure_evidence: recompositionData.failure_evidence,
    failure_analysis: recompositionData.failure_analysis,
    timestamp: recompositionData.timestamp || new Date().toISOString()
  };

  console.log('Triggering recomposition:', { 
    compositionId: payload.composition_id, 
    triggerType: payload.trigger_type 
  });

  const response = await makeRequest(API_CONFIG.ENDPOINTS.RECOMPOSE, {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  console.log('Recomposition triggered:', {
    originalId: payload.composition_id,
    newCompositionId: response.new_composition_id,
    status: response.status
  });

  return response;
};

// In-memory store for confirmed compositions (for UI tracking)
const confirmedCompositions = new Map();

/**
 * Track a confirmed composition locally
 * @param {string} compositionId - UUID of the composition
 * @param {Object} compositionData - Full composition data
 */
export const trackConfirmedComposition = (compositionId, compositionData) => {
  confirmedCompositions.set(compositionId, {
    ...compositionData,
    confirmedAt: new Date().toISOString(),
    status: 'deployed'
  });
};

/**
 * Get locally tracked composition
 * @param {string} compositionId - UUID of the composition
 * @returns {Object|null} Tracked composition data
 */
export const getTrackedComposition = (compositionId) => {
  return confirmedCompositions.get(compositionId) || null;
};

/**
 * Get all locally tracked compositions
 * @returns {Array} Array of confirmed compositions
 */
export const getAllTrackedCompositions = () => {
  return Array.from(confirmedCompositions.entries()).map(([id, data]) => ({
    compositionId: id,
    ...data
  }));
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