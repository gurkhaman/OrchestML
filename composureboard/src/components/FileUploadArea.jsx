import { useState, useRef } from 'react';
import { UPLOAD_CONFIG } from '../config/constants.js';

/**
 * FileUploadArea Component
 * 
 * Handles file upload with text extraction and preview:
 * - Drag & drop or click to upload files
 * - Text extraction from .md and .txt files
 * - File content preview and validation
 * - Integration with composition API
 */
const FileUploadArea = ({ onFileProcessed }) => {
  const [uploadState, setUploadState] = useState('idle'); // idle, reading, loaded, error
  const [fileName, setFileName] = useState('');
  const [fileContent, setFileContent] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  
  const formatText = `Formats accepted are ${UPLOAD_CONFIG.ACCEPTED_FORMATS.join(' and ')}`;
  
  /**
   * Validates if the uploaded file type is supported
   */
  const validateFile = (file) => {
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!UPLOAD_CONFIG.ACCEPTED_FORMATS.includes(extension)) {
      throw new Error(`File type ${extension} not supported. ${formatText}`);
    }
    
    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      throw new Error('File size too large. Please upload files smaller than 10MB.');
    }
  };
  
  /**
   * Reads file content as text
   */
  const readFileContent = async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        const content = e.target.result;
        if (content && content.trim().length > 0) {
          resolve(content);
        } else {
          reject(new Error('File appears to be empty'));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('Failed to read file'));
      };
      
      reader.readAsText(file);
    });
  };
  
  /**
   * Processes uploaded file
   */
  const processFile = async (file) => {
    try {
      setUploadState('reading');
      setError('');
      
      // Validate file
      validateFile(file);
      
      // Read content
      const content = await readFileContent(file);
      
      // Update state
      setFileName(file.name);
      setFileContent(content);
      setUploadState('loaded');
      
      // Notify parent component
      if (onFileProcessed) {
        onFileProcessed({
          fileName: file.name,
          content: content,
          size: file.size
        });
      }
      
    } catch (err) {
      setError(err.message);
      setUploadState('error');
      setFileName('');
      setFileContent('');
    }
  };
  
  /**
   * Handle file drop
   */
  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      processFile(files[0]);
    }
  };
  
  /**
   * Handle file input change
   */
  const handleFileInput = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      processFile(files[0]);
    }
  };
  
  /**
   * Handle drag over
   */
  const handleDragOver = (e) => {
    e.preventDefault();
  };
  
  /**
   * Handle click to upload
   */
  const handleClick = () => {
    fileInputRef.current?.click();
  };
  
  /**
   * Clear uploaded file
   */
  const handleCancel = () => {
    setUploadState('idle');
    setFileName('');
    setFileContent('');
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (onFileProcessed) {
      onFileProcessed(null);
    }
  };
  
  /**
   * Continue with current file
   */
  const handleContinue = () => {
    if (uploadState === 'loaded' && onFileProcessed) {
      onFileProcessed({
        fileName,
        content: fileContent,
        size: fileContent.length,
        confirmed: true
      });
    }
  };
  
  return (
    <section className="upload-section">
      <div className="upload-container">
        <div className="upload-header">
          <h2 className="upload-title">{UPLOAD_CONFIG.SECTION_TITLE}</h2>
          <p className="upload-subtitle">{UPLOAD_CONFIG.SECTION_SUBTITLE}</p>
        </div>
        
        {uploadState === 'idle' && (
          <div 
            className="upload-dropzone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={handleClick}
          >
            <div className="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7,10 12,15 17,10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </div>
            <div className="upload-text">
              <p className="upload-main-text">{UPLOAD_CONFIG.PLACEHOLDER_TEXT}</p>
              <p className="upload-helper-text">{formatText}</p>
            </div>
            <input 
              ref={fileInputRef}
              type="file"
              accept={UPLOAD_CONFIG.ACCEPTED_FORMATS.join(',')}
              onChange={handleFileInput}
              style={{ display: 'none' }}
            />
          </div>
        )}
        
        {uploadState === 'reading' && (
          <div className="upload-loading">
            <div className="loading-spinner"></div>
            <p>Reading file content...</p>
          </div>
        )}
        
        {uploadState === 'loaded' && (
          <div className="upload-preview">
            <div className="file-info">
              <h4>File loaded: {fileName}</h4>
              <p>Content length: {fileContent.length} characters</p>
            </div>
            <div className="content-preview">
              <h5>Content Preview:</h5>
              <pre className="content-text">
                {fileContent.slice(0, 500)}
                {fileContent.length > 500 && '...'}
              </pre>
            </div>
          </div>
        )}
        
        {uploadState === 'error' && (
          <div className="upload-error">
            <div className="error-icon">⚠️</div>
            <p className="error-message">{error}</p>
            <button className="retry-btn" onClick={() => setUploadState('idle')}>
              Try Again
            </button>
          </div>
        )}
        
        <div className="upload-actions">
          <button 
            className="upload-btn cancel" 
            onClick={handleCancel}
            disabled={uploadState === 'reading'}
          >
            Cancel
          </button>
          <button 
            className="upload-btn continue" 
            onClick={handleContinue}
            disabled={uploadState !== 'loaded'}
          >
            Continue
          </button>
        </div>
      </div>
    </section>
  );
};

export default FileUploadArea;