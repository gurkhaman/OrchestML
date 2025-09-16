/**
 * Graph layout utilities
 * Handles positioning and arrangement of nodes in the React Flow graph
 */

import { LAYOUT_CONFIG } from '../config/constants.js';

/**
 * Calculates hierarchical levels for nodes based on their dependencies
 * @param {Map} nodeMap - Map of node IDs to node objects
 * @param {Array} edges - Array of edge objects representing dependencies
 */
const calculateHierarchicalLevels = (nodeMap, edges) => {
  let changed = true;
  let iterations = 0;
  const maxIterations = 100; // Prevent infinite loops
  
  while (changed && iterations < maxIterations) {
    changed = false;
    iterations++;
    
    edges.forEach(edge => {
      const sourceNode = nodeMap.get(edge.source);
      const targetNode = nodeMap.get(edge.target);
      
      if (sourceNode && targetNode && targetNode.level <= sourceNode.level) {
        targetNode.level = sourceNode.level + 1;
        changed = true;
      }
    });
  }
  
  if (iterations >= maxIterations) {
    console.warn('Layout calculation reached maximum iterations, possible circular dependency');
  }
};

/**
 * Groups nodes by their hierarchical level
 * @param {Array} nodes - Array of node objects
 * @returns {Map} Map of level numbers to arrays of nodes
 */
const groupNodesByLevel = (nodes) => {
  const levelGroups = new Map();
  
  nodes.forEach(node => {
    if (!levelGroups.has(node.level)) {
      levelGroups.set(node.level, []);
    }
    levelGroups.get(node.level).push(node);
  });
  
  return levelGroups;
};

/**
 * Positions nodes in a horizontal hierarchical layout
 * @param {Array} nodes - Array of React Flow node objects
 * @param {Array} edges - Array of React Flow edge objects
 * @returns {Array} Array of positioned node objects
 */
export const layoutNodesHorizontally = (nodes, edges) => {
  // Initialize node map with default positions and levels
  const nodeMap = new Map();
  nodes.forEach(node => {
    nodeMap.set(node.id, { 
      ...node, 
      level: 0, 
      position: { x: 0, y: 0 } 
    });
  });
  
  // Calculate hierarchical levels based on dependencies
  calculateHierarchicalLevels(nodeMap, edges);
  
  // Group nodes by level for positioning
  const levelGroups = groupNodesByLevel(Array.from(nodeMap.values()));
  
  // Position nodes with proper spacing
  Array.from(levelGroups.entries()).forEach(([level, levelNodes]) => {
    const totalLevelHeight = levelNodes.length * LAYOUT_CONFIG.VERTICAL_SPACING;
    const startY = -totalLevelHeight / 2;
    
    levelNodes.forEach((node, index) => {
      node.position = {
        x: level * LAYOUT_CONFIG.HORIZONTAL_SPACING + LAYOUT_CONFIG.LAYOUT_PADDING,
        y: startY + (index * LAYOUT_CONFIG.VERTICAL_SPACING) + (LAYOUT_CONFIG.VERTICAL_SPACING / 2)
      };
    });
  });
  
  return Array.from(nodeMap.values());
};

/**
 * Validates that the layout configuration is sensible
 * @returns {boolean} True if configuration is valid
 */
export const validateLayoutConfig = () => {
  const { HORIZONTAL_SPACING, VERTICAL_SPACING, CARD_HEIGHT } = LAYOUT_CONFIG;
  
  if (VERTICAL_SPACING < CARD_HEIGHT) {
    console.warn('Vertical spacing is less than card height, nodes may overlap');
    return false;
  }
  
  if (HORIZONTAL_SPACING < 300) {
    console.warn('Horizontal spacing may be too small for wide service cards');
    return false;
  }
  
  return true;
};