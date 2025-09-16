/**
 * AlternativeSelector Component
 * 
 * Provides UI for selecting between different composition blueprint alternatives.
 * Each alternative represents a different approach to solving the same requirements
 * with varying complexity and service choices.
 * 
 * @param {Array} alternatives - Array of composition blueprint objects
 * @param {number} selectedIndex - Currently selected alternative index
 * @param {Function} onAlternativeChange - Callback when user selects different alternative
 */
const AlternativeSelector = ({ alternatives, selectedIndex, onAlternativeChange }) => {
  return (
    <div className="alternative-selector">
      <h3>Composition Alternatives ({alternatives.length})</h3>
      <div className="alternative-buttons">
        {alternatives.map((alt, index) => (
          <button
            key={index}
            className={`alternative-btn ${selectedIndex === index ? 'active' : ''}`}
            onClick={() => onAlternativeChange(index)}
          >
            <div className="alt-number">#{index + 1}</div>
            <div className="alt-info">
              <div className="alt-tasks">{alt.tasks.length} tasks</div>
              <div className="alt-desc">{alt.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AlternativeSelector;