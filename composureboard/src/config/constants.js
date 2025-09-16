/**
 * Application configuration constants
 * Centralized location for all configurable values
 */

// Layout Configuration
export const LAYOUT_CONFIG = {
  // Node positioning
  HORIZONTAL_SPACING: 450,
  VERTICAL_SPACING: 180,
  CARD_HEIGHT: 120,
  LAYOUT_PADDING: 50,
  
  // Viewport settings
  COMPOSITION_VIEWPORT_HEIGHT: 600,
  MAX_CONTAINER_WIDTH: 1400,
  SECTION_GAP: 60,
  CONTAINER_PADDING: 40,
};

// Application Metadata
export const APP_CONFIG = {
  TITLE: 'ComposureCI',
  SUBTITLE: 'Service Composition Visualizer',
  VERSION: '1.0.0',
  MODE: 'Mock Data Mode',
};

// File Upload Configuration
export const UPLOAD_CONFIG = {
  ACCEPTED_FORMATS: ['.md', '.txt'],
  SECTION_TITLE: '1. Upload Composition Requirement',
  SECTION_SUBTITLE: 'File Upload',
  PLACEHOLDER_TEXT: 'Click or drag file to this area to upload',
  HELPER_TEXT: 'Formats accepted are .md and .txt',
};

// Composition Configuration
export const COMPOSITION_CONFIG = {
  SECTION_TITLE: '2. Composition Generation',
  DEFAULT_ALTERNATIVE_INDEX: 0,
  REACT_FLOW_OPTIONS: {
    fitViewOptions: { 
      padding: 0.2, 
      maxZoom: 0.8,
      minZoom: 0.1
    },
  },
};

// Navigation Configuration
export const NAVIGATION_CONFIG = {
  TABS: [
    { id: 'flow', label: 'Flow', active: true },
    { id: 'services', label: 'Services', active: false },
  ],
};

// Service Node Configuration
export const SERVICE_CONFIG = {
  DEFAULT_VERSION: 'Version 1.0',
  GO_TO_SOURCE_TEXT: 'Go to source </>',
  HANDLE_IDS: {
    INPUT: 'input',
    OUTPUT: 'output',
  },
};