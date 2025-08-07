import axios from 'axios';

// Configure your FastAPI backend endpoint here
const API_BASE_URL = "http://127.0.0.1:8000"; // Update this with your actual backend URL

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout for audio processing
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

/**
 * Upload audio file for chord analysis using our FastAPI backend
 * @param {Object} audioFile - The audio file to upload
 * @param {number} confidence - Confidence threshold (default: 0.3)
 * @param {number} minDuration - Minimum duration threshold (default: 0.05)
 * @returns {Promise} Response data with chord analysis results
 */
export const uploadAudio = async (audioFile, confidence = 0.3, minDuration = 0.05) => {
  try {
    const formData = new FormData();
    formData.append('file', {
      uri: audioFile.uri,
      type: audioFile.type || 'audio/wav',
      name: audioFile.name || 'recording.wav',
    });

    const response = await apiClient.post(`/analyze?confidence=${confidence}&min_duration=${minDuration}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error uploading audio:', error);
    throw new Error(`Failed to upload audio: ${error.message}`);
  }
};

/**
 * Get music guidance from the LLM
 * @param {Object} queryData - Query data including user question and context
 * @returns {Promise} Response data with guidance text and TTS audio URL
 */
export const getGuidance = async (queryData) => {
  try {
    const response = await apiClient.post('/get-guidance', queryData, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error getting guidance:', error);
    throw new Error(`Failed to get guidance: ${error.message}`);
  }
};

/**
 * Get chord analysis from audio
 * @param {Object} audioData - Audio data for chord extraction
 * @returns {Promise} Response data with chord analysis
 */
export const analyzeChords = async (audioData) => {
  try {
    const response = await apiClient.post('/analyze-chords', audioData);
    return response.data;
  } catch (error) {
    console.error('Error analyzing chords:', error);
    throw new Error(`Failed to analyze chords: ${error.message}`);
  }
};

/**
 * Health check endpoint
 * @returns {Promise} Server health status
 */
export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/');
    return { status: 'online' };
  } catch (error) {
    console.error('Health check failed:', error);
    throw new Error(`Server health check failed: ${error.message}`);
  }
};

/**
 * Query the RAG system for music guidance
 * @param {string} question - The user's question
 * @param {Object} context - Additional context (chord data, etc.)
 * @returns {Promise} Response with guidance text
 */
export const queryRAG = async (question, context = {}) => {
  try {
    const response = await apiClient.post('/rag-query', {
      question,
      context
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return response.data;
  } catch (error) {
    console.error('Error querying RAG:', error);
    throw new Error(`Failed to get RAG response: ${error.message}`);
  }
};