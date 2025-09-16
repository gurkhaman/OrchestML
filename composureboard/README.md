# ComposureCI Frontend

A React-based web interface for automated ML service composition visualization using React Flow.

## Project Structure

```
src/
├── components/           # React components
│   ├── Header.jsx       # Main application header
│   ├── FileUploadArea.jsx # File upload interface (placeholder)
│   ├── CompositionSection.jsx # Main composition visualization
│   ├── ServiceNode.jsx  # Individual service card component
│   ├── AlternativeSelector.jsx # Blueprint alternative chooser
│   └── ExportPanel.jsx  # JSON export functionality
├── config/
│   └── constants.js     # Application configuration constants
├── utils/
│   ├── serviceUtils.js  # Service data processing utilities
│   └── layoutUtils.js   # Graph layout algorithms
├── App.jsx             # Root application component
├── main.jsx            # Application entry point
├── styles.css          # Global styles and component styling
└── mockData.js         # Test data for composition blueprints
```

## Key Features

### Composition Visualization
- **Interactive React Flow graph** with custom service node cards
- **Hierarchical layout algorithm** for optimal node positioning
- **Colored connection handles** (green for input, orange for output)
- **Multiple composition alternatives** with easy switching

### Service Node Cards
- Professional card design with service information
- Source repository links (GitHub, Hugging Face, ROS Index)
- Input/output type indicators
- Version information display

### Export Functionality
- JSON download of composition blueprints
- Clipboard copy functionality
- CompositionBlueprint schema compliance

## Configuration

All configurable values are centralized in `src/config/constants.js`:

- **Layout settings**: Node spacing, viewport dimensions
- **Application metadata**: Titles, version info
- **UI text content**: Labels, placeholder text
- **Navigation structure**: Tab configuration

## Architecture Decisions

### Component Organization
- **Separation of concerns**: Each component has a single responsibility
- **Configuration-driven**: Minimal hardcoded values
- **Utility functions**: Reusable logic extracted to utility files

### Styling Approach
- **CSS-in-CSS**: No inline styles, all styling in dedicated CSS file
- **CSS variables**: Theme colors and layout values configurable
- **BEM-like naming**: Clear, semantic class names
- **Responsive design**: Mobile-friendly breakpoints

### State Management
- **React hooks**: useState and useEffect for local state
- **Props drilling**: Simple parent-child communication
- **No external state library**: Keeps dependencies minimal

## Mock Data

The application includes comprehensive test data:

1. **Simple Linear Pipeline** (3 nodes) - Basic sequential processing
2. **Branching Pipeline** (5 nodes) - Parallel processing with convergence
3. **Complex Pipeline** (7 nodes) - Multiple analysis branches
4. **Massive Pipeline** (12 nodes) - Stress test with complex dependencies

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Integration

The frontend is designed to integrate with the ComposureCI orchestrator API:

- **Expected endpoint**: `POST /api/v1/compose`
- **Input format**: `{ requirements: string }`
- **Output format**: `CompositionBlueprintAgentResponse`

Replace mock data imports in `CompositionSection.jsx` with actual API calls when backend is ready.

## Browser Support

- Modern browsers with ES2020+ support
- React 19+ compatibility
- CSS Grid and Flexbox support required
