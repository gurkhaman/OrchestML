/**
 * ComposureCI - Service Composition Visualizer
 * 
 * Main application component that orchestrates the entire user interface:
 * - Header with navigation and branding
 * - File upload area for composition requirements
 * - Interactive composition graph visualization
 * 
 * Supports both file upload mode and mock data mode for demonstration.
 * 
 * @author ComposureCI Team
 * @version 1.0.0
 */

import { useState } from 'react';
import '@xyflow/react/dist/style.css';
import Header from './components/Header.jsx';
import FileUploadArea from './components/FileUploadArea.jsx';
import CompositionSection from './components/CompositionSection.jsx';

/**
 * App Component
 * 
 * Root application component that manages the application state
 * and coordinates between file upload and composition visualization
 */
export default function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [appMode, setAppMode] = useState('mock'); // 'mock' or 'upload'
  
  /**
   * Handle file upload completion
   */
  const handleFileProcessed = (fileData) => {
    if (fileData) {
      setUploadedFile(fileData);
      if (fileData.confirmed) {
        setAppMode('upload');
      }
    } else {
      setUploadedFile(null);
      setAppMode('mock');
    }
  };
  
  /**
   * Switch back to mock mode
   */
  const handleUseMockData = () => {
    setAppMode('mock');
    setUploadedFile(null);
  };
  
  return (
    <div className="app">
      <Header />
      
      <main className="app-main">
        <div className="app-container">
          <FileUploadArea onFileProcessed={handleFileProcessed} />
          <CompositionSection 
            mode={appMode}
            uploadedFile={uploadedFile}
            onUseMockData={handleUseMockData}
          />
        </div>
      </main>
    </div>
  );
}