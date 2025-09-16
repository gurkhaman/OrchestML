/**
 * Service-related utility functions
 * Centralizes logic for service data processing and mapping
 */

/**
 * Maps service names to their source repository information
 * In a real implementation, this would come from the API
 */
const SERVICE_SOURCE_MAP = {
  'stable-diffusion-x4-upscaler': { 
    type: 'Hugging Face', 
    url: 'https://huggingface.co/stabilityai/stable-diffusion-x4-upscaler' 
  },
  'resnet-50': { 
    type: 'GitHub', 
    url: 'https://github.com/pytorch/vision' 
  },
  'yolov10s': { 
    type: 'GitHub', 
    url: 'https://github.com/THU-MIG/yolov10' 
  },
  'detr-resnet-101': { 
    type: 'Hugging Face', 
    url: 'https://huggingface.co/facebook/detr-resnet-101' 
  },
  'swinv2-tiny-patch4-window16-256': { 
    type: 'Hugging Face', 
    url: 'https://huggingface.co/microsoft/swinv2-tiny-patch4-window16-256' 
  },
  'nav2': { 
    type: 'ROS Index', 
    url: 'https://index.ros.org/r/navigation2/' 
  },
  'vosk': { 
    type: 'GitHub', 
    url: 'https://github.com/alphacep/vosk-api' 
  },
};

/**
 * Default source info for unknown services
 */
const DEFAULT_SOURCE = { type: 'GitHub', url: '#' };

/**
 * Gets source repository information for a service
 * @param {string} serviceName - Name of the service
 * @returns {Object} Source information with type and URL
 */
export const getSourceInfo = (serviceName) => {
  return SERVICE_SOURCE_MAP[serviceName] || DEFAULT_SOURCE;
};

/**
 * Determines input type based on task arguments
 * @param {Object} args - Task arguments object
 * @returns {string} Input type string
 */
export const getInputType = (args) => {
  if (args.image) return 'Image';
  if (args.text) return 'Text'; 
  if (args.document) return 'Document';
  return 'Data';
};

/**
 * Determines output type based on service name and arguments
 * Uses heuristics to infer output type from service functionality
 * @param {Object} args - Task arguments object
 * @param {string} serviceName - Name of the service
 * @returns {string} Output type string
 */
export const getOutputType = (args, serviceName) => {
  // Classification services
  if (serviceName.includes('classification') || serviceName.includes('resnet')) {
    return 'Labels';
  }
  
  // Detection services
  if (serviceName.includes('detection') || serviceName.includes('yolo')) {
    return 'Bboxes';
  }
  
  // Image generation/processing services
  if (serviceName.includes('upscaler') || serviceName.includes('diffusion')) {
    return 'Image';
  }
  
  // Navigation services
  if (serviceName.includes('nav')) {
    return 'Path';
  }
  
  // Speech/Audio services
  if (serviceName.includes('vosk') || serviceName.includes('speech')) {
    return 'Text';
  }
  
  return 'Data';
};

/**
 * Opens a URL in a new browser tab
 * @param {string} url - URL to open
 */
export const openExternalLink = (url) => {
  if (url && url !== '#') {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};