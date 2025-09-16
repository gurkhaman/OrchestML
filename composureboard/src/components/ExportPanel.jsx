/**
 * ExportPanel Component
 * 
 * Provides functionality to export composition blueprints in JSON format.
 * Users can either download the blueprint as a file or copy it to clipboard
 * for integration with other tools and systems.
 * 
 * @param {Object} blueprint - The composition blueprint object to export
 * @param {number} alternativeIndex - Index of the current alternative (for filename)
 */
const ExportPanel = ({ blueprint, alternativeIndex }) => {
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
  
  return (
    <div className="export-panel">
      <h4>Export Blueprint #{alternativeIndex + 1}</h4>
      <div className="export-buttons">
        <button onClick={exportToJson} className="export-btn download">
          📁 Download JSON
        </button>
        <button onClick={copyToClipboard} className="export-btn copy">
          📋 Copy to Clipboard
        </button>
      </div>
      <div className="export-info">
        <div>Tasks: {blueprint.tasks.length}</div>
        <div>Format: CompositionBlueprint JSON</div>
      </div>
    </div>
  );
};

export default ExportPanel;