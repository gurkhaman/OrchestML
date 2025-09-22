/**
 * ConfirmationPanel Component
 * 
 * Provides interface for users to confirm and deploy composition blueprints.
 * Captures deployment context and enables monitoring integration.
 * 
 * @param {Object} blueprint - The composition blueprint to deploy
 * @param {string} compositionId - UUID of the composition
 * @param {number} alternativeIndex - Index of selected alternative
 * @param {Function} onConfirm - Callback when user confirms deployment
 * @param {Function} onCancel - Callback when user cancels
 * @param {boolean} isConfirming - Loading state during confirmation
 */
import { useState } from 'react';

const ConfirmationPanel = ({ 
  blueprint, 
  compositionId, 
  alternativeIndex,
  onConfirm, 
  onCancel, 
  isConfirming = false 
}) => {
  // Simplified deployment context for now - can be expanded later
  const [deploymentContext] = useState({
    environment: 'development',
    monitoringEnabled: true,
    autoRecomposition: true
  });

  const handleConfirmClick = () => {
    onConfirm(deploymentContext);
  };

  return (
    <div className="confirmation-panel">
      <div className="confirmation-header">
        <h3>🚀 Confirm Deployment</h3>
        <p>Review and deploy Blueprint #{alternativeIndex + 1}</p>
      </div>

      <div className="confirmation-content">
        {/* Blueprint Summary */}
        <div className="blueprint-summary">
          <h4>📋 Blueprint Summary</h4>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="label">Composition ID:</span>
              <code className="composition-id">{compositionId}</code>
            </div>
            <div className="summary-item">
              <span className="label">Tasks:</span>
              <span className="value">{blueprint.tasks.length} services</span>
            </div>
            <div className="summary-item">
              <span className="label">Description:</span>
              <span className="value">{blueprint.description || 'No description'}</span>
            </div>
          </div>

          {/* Task List Preview */}
          <div className="task-preview">
            <h5>Service Pipeline:</h5>
            <div className="task-list">
              {blueprint.tasks.map(task => (
                <div key={task.id} className="task-item">
                  <span className="task-id">#{task.id}</span>
                  <span className="task-service">{task.service_name}</span>
                  <span className="task-name">{task.task}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Deployment Configuration - COMMENTED OUT FOR NOW (can be re-enabled later) */}
        {/* 
        <div className="deployment-config">
          <h4>⚙️ Deployment Configuration</h4>
          
          <div className="config-grid">
            <div className="config-field">
              <label htmlFor="environment">Environment:</label>
              <select 
                id="environment"
                value={deploymentContext.environment}
                onChange={(e) => handleInputChange('environment', e.target.value)}
                disabled={isConfirming}
              >
                <option value="development">Development</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
            </div>

            <div className="config-field checkbox-field">
              <label>
                <input
                  type="checkbox"
                  checked={deploymentContext.monitoringEnabled}
                  onChange={(e) => handleInputChange('monitoringEnabled', e.target.checked)}
                  disabled={isConfirming}
                />
                Enable Performance Monitoring
              </label>
            </div>

            <div className="config-field checkbox-field">
              <label>
                <input
                  type="checkbox"
                  checked={deploymentContext.autoRecomposition}
                  onChange={(e) => handleInputChange('autoRecomposition', e.target.checked)}
                  disabled={isConfirming}
                />
                Enable Auto-Recomposition
              </label>
            </div>
          </div>

          <div className="performance-thresholds">
            <h5>📊 Performance Thresholds</h5>
            <div className="threshold-grid">
              <div className="threshold-field">
                <label htmlFor="maxExecutionTime">Max Execution Time (seconds):</label>
                <input
                  id="maxExecutionTime"
                  type="number"
                  value={deploymentContext.performanceThresholds.maxExecutionTime}
                  onChange={(e) => handleInputChange('performanceThresholds.maxExecutionTime', parseInt(e.target.value))}
                  disabled={isConfirming}
                  min="10"
                  max="3600"
                />
              </div>
              <div className="threshold-field">
                <label htmlFor="errorRate">Max Error Rate (0.0-1.0):</label>
                <input
                  id="errorRate"
                  type="number"
                  step="0.01"
                  value={deploymentContext.performanceThresholds.errorRate}
                  onChange={(e) => handleInputChange('performanceThresholds.errorRate', parseFloat(e.target.value))}
                  disabled={isConfirming}
                  min="0"
                  max="1"
                />
              </div>
            </div>
          </div>

          <div className="config-field">
            <label htmlFor="description">Deployment Notes (optional):</label>
            <textarea
              id="description"
              value={deploymentContext.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Add any notes about this deployment..."
              disabled={isConfirming}
              rows="3"
            />
          </div>
        </div>
        */}
      </div>

      {/* Action Buttons */}
      <div className="confirmation-actions">
        <button 
          className="cancel-btn" 
          onClick={onCancel}
          disabled={isConfirming}
        >
          Cancel
        </button>
        <button 
          className="confirm-btn"
          onClick={handleConfirmClick}
          disabled={isConfirming}
        >
          {isConfirming ? (
            <>
              <div className="spinner"></div>
              Deploying...
            </>
          ) : (
            <>
              🚀 Confirm & Deploy
            </>
          )}
        </button>
      </div>

      {/* Info Box */}
      <div className="confirmation-info">
        <p>
          <strong>What happens next?</strong><br/>
          • Your composition will be registered with ID: <code>{compositionId}</code><br/>
          • {deploymentContext.monitoringEnabled ? 'Performance monitoring will track execution metrics' : 'No monitoring will be enabled'}<br/>
          • {deploymentContext.autoRecomposition ? 'System will automatically adapt if performance degrades' : 'Manual intervention required for performance issues'}
        </p>
      </div>
    </div>
  );
};

export default ConfirmationPanel;