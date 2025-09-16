import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { getSourceInfo, getInputType, getOutputType, openExternalLink } from '../utils/serviceUtils.js';
import { SERVICE_CONFIG } from '../config/constants.js';

/**
 * ServiceNode Component
 * 
 * Renders a service node card in the React Flow graph with:
 * - Service information (name, version, description)
 * - Input/Output type indicators
 * - Source repository information
 * - Connection handles for graph edges
 * 
 * @param {Object} props.data - Node data containing service information
 * @param {string} props.data.service_name - Name of the service
 * @param {string} props.data.task - Description of what the service does
 * @param {Object} props.data.args - Service arguments (image, text, document)
 * @param {number} props.data.taskId - Unique identifier for the task
 */
const ServiceNode = memo(({ data }) => {
  const sourceInfo = getSourceInfo(data.service_name);
  const inputType = getInputType(data.args);
  const outputType = getOutputType(data.args, data.service_name);
  
  const handleGoToSource = () => {
    openExternalLink(sourceInfo.url);
  };
  
  return (
    <div className="service-node-card">
      {/* Incoming Handle - Left */}
      <Handle 
        type="target" 
        position={Position.Left} 
        id={SERVICE_CONFIG.HANDLE_IDS.INPUT}
        className="handle-input"
      />
      
      <div className="service-card-content">
        {/* Header Section */}
        <div className="service-card-header">
          <div className="service-version">{SERVICE_CONFIG.DEFAULT_VERSION}</div>
          <div className="service-title">{data.service_name}</div>
        </div>
        
        {/* Description */}
        <div className="service-description">
          {data.task}
        </div>
        
        {/* Input/Output Section */}
        <div className="service-io-section">
          <div className="service-io-item">
            <span className="io-label">Source</span>
            <span className="io-value">{sourceInfo.type}</span>
          </div>
          <div className="service-io-item">
            <span className="io-label">Input</span>
            <span className="io-value">{inputType}</span>
          </div>
          <div className="service-io-item">
            <span className="io-label">Output</span>
            <span className="io-value">{outputType}</span>
          </div>
        </div>
        
        {/* Go to Source Button */}
        <button className="go-to-source-btn" onClick={handleGoToSource}>
          {SERVICE_CONFIG.GO_TO_SOURCE_TEXT}
        </button>
      </div>
      
      {/* Outgoing Handle - Right */}
      <Handle 
        type="source" 
        position={Position.Right} 
        id={SERVICE_CONFIG.HANDLE_IDS.OUTPUT}
        className="handle-output"
      />
    </div>
  );
});

ServiceNode.displayName = 'ServiceNode';

export default ServiceNode;