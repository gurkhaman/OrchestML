/**
 * ExportPanel Component
 * 
 * Provides functionality to export composition blueprints in JSON format and
 * confirm deployment to production systems.
 * 
 * @param {Object} blueprint - The composition blueprint object to export
 * @param {number} alternativeIndex - Index of the current alternative (for filename)
 * @param {Function} onConfirmDeployment - Callback to trigger deployment confirmation
 * @param {boolean} isDeployed - Whether this composition is already deployed
 * @param {string} compositionId - UUID of the composition (if available)
 */
const ExportPanel = ({ 
  blueprint, 
  alternativeIndex, 
  onConfirmDeployment, 
  isDeployed = false,
  compositionId 
}) => {
  const exportToJson = () => {
    const dataStr = JSON.stringify(blueprint, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `composition-blueprint-${alternativeIndex + 1}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };
  
  const copyToClipboard = async () => {
    const dataStr = JSON.stringify(blueprint, null, 2);
    try {
      await navigator.clipboard.writeText(dataStr);
      alert('Blueprint copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      alert('Failed to copy to clipboard. Please try the download option.');
    }
  };

  const copyCompositionId = async () => {
    if (!compositionId) return;
    try {
      await navigator.clipboard.writeText(compositionId);
      alert('Composition ID copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy composition ID:', err);
      alert('Failed to copy composition ID.');
    }
  };

  const handleConfirmDeployment = () => {
    if (onConfirmDeployment) {
      onConfirmDeployment();
    }
  };
  
  return (
    <div className="export-panel">
      <h4>
        {isDeployed ? (
          <>
            ✅ Deployed Blueprint #{alternativeIndex + 1}
          </>
        ) : (
          <>
            Export Blueprint #{alternativeIndex + 1}
          </>
        )}
      </h4>
      
      {/* Deployment Actions */}
      {!isDeployed && onConfirmDeployment && (
        <div className="deployment-actions">
          <button 
            onClick={handleConfirmDeployment} 
            className="deploy-btn primary"
          >
            🚀 Confirm & Deploy
          </button>
        </div>
      )}

      {/* Deployment Status */}
      {isDeployed && compositionId && (
        <div className="deployment-status">
          <div className="status-badge deployed">Deployed</div>
          <div className="composition-id">
            <span>ID: </span>
            <code onClick={copyCompositionId} className="clickable-id" title="Click to copy">
              {compositionId.slice(0, 8)}...
            </code>
          </div>
        </div>
      )}

      {/* Export Actions */}
      <div className="export-section">
        <h5>Export Options</h5>
        <div className="export-buttons">
          <button onClick={exportToJson} className="export-btn download">
            📁 Download JSON
          </button>
          <button onClick={copyToClipboard} className="export-btn copy">
            📋 Copy Blueprint
          </button>
          {compositionId && (
            <button onClick={copyCompositionId} className="export-btn copy">
              🔗 Copy ID
            </button>
          )}
        </div>
      </div>

      <div className="export-info">
        <div>Tasks: {blueprint.tasks.length}</div>
        <div>Format: CompositionBlueprint JSON</div>
        {isDeployed && <div>Status: Production Ready</div>}
      </div>
    </div>
  );
};

export default ExportPanel;