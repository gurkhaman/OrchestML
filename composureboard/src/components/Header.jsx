import { APP_CONFIG, NAVIGATION_CONFIG } from '../config/constants.js';

/**
 * Header Component
 * 
 * Renders the main application header with:
 * - Application branding and title
 * - Navigation tabs
 * - Status indicator
 * - External link buttons
 */
const Header = () => {
  return (
    <header className="app-header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo-section">
            <h1 className="app-title">{APP_CONFIG.TITLE}</h1>
            <span className="app-subtitle">{APP_CONFIG.SUBTITLE}</span>
          </div>
        </div>
        
        <div className="header-center">
          <nav className="header-nav">
            {NAVIGATION_CONFIG.TABS.map((tab) => (
              <button 
                key={tab.id}
                className={`nav-button ${tab.active ? 'active' : ''}`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        
        <div className="header-right">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span className="status-text">{APP_CONFIG.MODE}</span>
          </div>
          <button className="github-button">
            <span>GitHub</span>
            <span className="icon-placeholder">[🔗]</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;