import { useState, useCallback, useEffect } from 'react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
import { mockCompositions, convertToReactFlowFormat } from '../mockData.js';
import { layoutNodesHorizontally, validateLayoutConfig } from '../utils/layoutUtils.js';
import { COMPOSITION_CONFIG, LAYOUT_CONFIG } from '../config/constants.js';
import ServiceNode from './ServiceNode.jsx';
import AlternativeSelector from './AlternativeSelector.jsx';
import ExportPanel from './ExportPanel.jsx';

const nodeTypes = {
  custom: ServiceNode,
};

/**
 * CompositionSection Component
 * 
 * Renders the composition generation section with:
 * - Support for both mock data and API-generated compositions
 * - Alternative selector for switching between compositions
 * - Export panel for downloading/copying blueprints
 * - Interactive React Flow graph visualization
 * - Loading states and error handling
 */
const CompositionSection = ({ mode = 'mock', uploadedFile = null, onUseMockData }) => {
  const [selectedAlternative, setSelectedAlternative] = useState(COMPOSITION_CONFIG.DEFAULT_ALTERNATIVE_INDEX);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [compositions, setCompositions] = useState(mockCompositions);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Validate layout configuration on component mount
  useEffect(() => {
    validateLayoutConfig();
  }, []);
  
  // Handle mode changes and file uploads
  useEffect(() => {
    if (mode === 'upload' && uploadedFile?.confirmed) {
      generateComposition(uploadedFile.content);
    } else if (mode === 'mock') {
      setCompositions(mockCompositions);
      setSelectedAlternative(COMPOSITION_CONFIG.DEFAULT_ALTERNATIVE_INDEX);
      setError(null);
    }
  }, [mode, uploadedFile]);
  
  // Update visualization when compositions or selection changes
  useEffect(() => {
    if (compositions?.alternatives && compositions.alternatives.length > 0) {
      const currentBlueprint = compositions.alternatives[selectedAlternative];
      if (currentBlueprint) {
        const { nodes, edges } = convertToReactFlowFormat(currentBlueprint);
        const layoutedNodes = layoutNodesHorizontally(nodes, edges);
        setNodes(layoutedNodes);
        setEdges(edges);
      }
    }
  }, [compositions, selectedAlternative]);
  
  /**
   * Generate composition from uploaded file content
   */
  const generateComposition = async (requirements) => {
    setLoading(true);
    setError(null);
    
    try {
      // Import API service dynamically to avoid import issues during build
      const { submitComposition, convertApiResponseToMockFormat } = await import('../utils/apiService.js');
      
      console.log('Generating composition for requirements:', requirements.slice(0, 100) + '...');
      
      const response = await submitComposition(requirements);
      const convertedCompositions = convertApiResponseToMockFormat(response);
      
      setCompositions(convertedCompositions);
      setSelectedAlternative(0);
      
      console.log('Composition generated successfully:', {
        alternatives: convertedCompositions.alternatives.length
      });
      
    } catch (err) {
      console.error('Composition generation failed:', err);
      setError(err.message || 'Failed to generate composition');
      
      // Fallback to mock data on API error
      setCompositions(mockCompositions);
      setSelectedAlternative(0);
    } finally {
      setLoading(false);
    }
  };
  
  const onNodesChange = useCallback(
    (changes) => setNodes((nodesSnapshot) => applyNodeChanges(changes, nodesSnapshot)),
    [],
  );
  const onEdgesChange = useCallback(
    (changes) => setEdges((edgesSnapshot) => applyEdgeChanges(changes, edgesSnapshot)),
    [],
  );
  const onConnect = useCallback(
    (params) => setEdges((edgesSnapshot) => addEdge(params, edgesSnapshot)),
    [],
  );
  
  const handleAlternativeChange = (index) => {
    setSelectedAlternative(index);
  };

  return (
    <section className="composition-section">
      <div className="composition-header">
        <h2 className="composition-title">{COMPOSITION_CONFIG.SECTION_TITLE}</h2>
        
        {/* Mode indicator and controls */}
        <div className="composition-mode">
          {mode === 'upload' && uploadedFile && (
            <div className="mode-info">
              <span className="mode-badge upload">File Mode</span>
              <span className="file-name">{uploadedFile.fileName}</span>
              <button className="mode-switch-btn" onClick={onUseMockData}>
                Use Mock Data
              </button>
            </div>
          )}
          {mode === 'mock' && (
            <div className="mode-info">
              <span className="mode-badge mock">Mock Data Mode</span>
            </div>
          )}
        </div>
        
        {/* Loading state */}
        {loading && (
          <div className="composition-loading">
            <div className="loading-spinner"></div>
            <p>Generating composition from your requirements...</p>
          </div>
        )}
        
        {/* Error state */}
        {error && (
          <div className="composition-error">
            <div className="error-message">
              <strong>Composition Generation Failed:</strong> {error}
            </div>
            <p>Showing mock data instead. Please check if the orchestrator service is running.</p>
          </div>
        )}
        
        {/* Controls - only show when not loading */}
        {!loading && compositions?.alternatives && (
          <div className="composition-controls">
            <div className="composition-controls-left">
              <AlternativeSelector 
                alternatives={compositions.alternatives}
                selectedIndex={selectedAlternative}
                onAlternativeChange={handleAlternativeChange}
              />
            </div>
            <div className="composition-controls-right">
              <ExportPanel 
                blueprint={compositions.alternatives[selectedAlternative]}
                alternativeIndex={selectedAlternative}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Viewport - always show, but empty when loading */}
      <div className="composition-viewport">
        {!loading && nodes.length > 0 ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={COMPOSITION_CONFIG.REACT_FLOW_OPTIONS.fitViewOptions}
          >
            <Controls />
            <Background />
          </ReactFlow>
        ) : loading ? (
          <div className="viewport-loading">
            <div className="loading-content">
              <div className="loading-spinner large"></div>
              <p>Processing your requirements...</p>
              <p className="loading-subtitle">This may take 30-60 seconds</p>
            </div>
          </div>
        ) : (
          <div className="viewport-empty">
            <p>No composition data available</p>
          </div>
        )}
      </div>
    </section>
  );
};

export default CompositionSection;