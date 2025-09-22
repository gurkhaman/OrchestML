import { useState, useCallback, useEffect } from 'react';
import { ReactFlow, Controls, Background, applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
import { mockCompositions, convertToReactFlowFormat } from '../mockData.js';
import { layoutNodesHorizontally, validateLayoutConfig } from '../utils/layoutUtils.js';
import { COMPOSITION_CONFIG, LAYOUT_CONFIG } from '../config/constants.js';
import ServiceNode from './ServiceNode.jsx';
import AlternativeSelector from './AlternativeSelector.jsx';
import ExportPanel from './ExportPanel.jsx';
import ConfirmationPanel from './ConfirmationPanel.jsx';

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
  
  // Confirmation workflow state
  const [confirmationMode, setConfirmationMode] = useState(false);
  const [confirmedComposition, setConfirmedComposition] = useState(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  
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
    setConfirmationMode(false);
    setConfirmedComposition(null);
    setDeploymentStatus(null);
    
    try {
      // Import API service dynamically to avoid import issues during build
      const { submitComposition, convertApiResponseToMockFormat } = await import('../utils/apiService.js');
      
      console.log('Generating composition for requirements:', requirements.slice(0, 100) + '...');
      
      const response = await submitComposition(requirements);
      const convertedCompositions = convertApiResponseToMockFormat(response);
      
      setCompositions(convertedCompositions);
      setSelectedAlternative(0);
      
      console.log('Composition generated successfully:', {
        alternatives: convertedCompositions.alternatives.length,
        compositionId: convertedCompositions.metadata.compositionId
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

  /**
   * Handle composition confirmation
   */
  const handleConfirmDeployment = async (deploymentContext) => {
    setIsConfirming(true);
    setError(null);
    
    try {
      const { confirmComposition, trackConfirmedComposition } = await import('../utils/apiService.js');
      
      // Use orchestrator-generated composition ID, not UI-generated
      const compositionId = compositions.metadata?.compositionId;
      if (!compositionId) {
        throw new Error('No composition ID available from orchestrator');
      }
      
      const selectedBlueprint = compositions.alternatives[selectedAlternative];
      
      const confirmationData = {
        blueprint: selectedBlueprint,
        deploymentContext,
        originalRequirements: uploadedFile?.content || 'Mock requirements',
        selectedAlternativeIndex: selectedAlternative
      };
      
      console.log('Confirming deployment for composition:', compositionId);
      
      const response = await confirmComposition(compositionId, confirmationData);
      
      // Track the confirmed composition locally
      trackConfirmedComposition(compositionId, {
        blueprint: selectedBlueprint,
        deploymentContext,
        response
      });
      
      setConfirmedComposition({
        compositionId,
        ...response,
        blueprint: selectedBlueprint,
        deploymentContext
      });
      
      setConfirmationMode(false);
      setDeploymentStatus('deployed');
      
      console.log('Composition deployed successfully:', response);
      
    } catch (err) {
      console.error('Deployment confirmation failed:', err);
      setError(`Deployment failed: ${err.message}`);
    } finally {
      setIsConfirming(false);
    }
  };

  /**
   * Handle confirmation cancellation
   */
  const handleConfirmationCancel = () => {
    setConfirmationMode(false);
    setError(null);
  };

  /**
   * Show confirmation panel
   */
  const handleShowConfirmation = () => {
    setConfirmationMode(true);
    setError(null);
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
        
        {/* Deployment Status */}
        {deploymentStatus && (
          <div className={`deployment-status ${deploymentStatus}`}>
            {deploymentStatus === 'deployed' && confirmedComposition && (
              <div className="status-success">
                ✅ <strong>Composition Deployed Successfully!</strong>
                <div className="status-details">
                  <span>ID: <code>{confirmedComposition.compositionId}</code></span>
                  <span>Environment: {confirmedComposition.deploymentContext.environment}</span>
                  <span>Monitoring: {confirmedComposition.deploymentContext.monitoringEnabled ? 'Enabled' : 'Disabled'}</span>
                </div>
              </div>
            )}

          </div>
        )}



        {/* Controls - only show when not loading and not in confirmation mode */}
        {!loading && !confirmationMode && compositions?.alternatives && (
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
                onConfirmDeployment={handleShowConfirmation}
                isDeployed={deploymentStatus === 'deployed'}
                compositionId={compositions.metadata?.compositionId}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Confirmation Panel */}
      {confirmationMode && compositions?.alternatives && (
        <div className="confirmation-overlay">
          <ConfirmationPanel
            blueprint={compositions.alternatives[selectedAlternative]}
            compositionId={compositions.metadata?.compositionId || 'pending-generation'}
            alternativeIndex={selectedAlternative}
            onConfirm={handleConfirmDeployment}
            onCancel={handleConfirmationCancel}
            isConfirming={isConfirming}
          />
        </div>
      )}

      {/* Viewport - always show, but empty when loading */}
      <div className="composition-viewport">
        {!loading && !confirmationMode && nodes.length > 0 ? (
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
        ) : confirmationMode ? (
          <div className="viewport-confirmation">
            <p>Review deployment configuration above</p>
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