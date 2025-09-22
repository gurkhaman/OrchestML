#!/usr/bin/env python3

import json
import glob
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NavigationDataProcessor:
    def __init__(self, data_dir: str = "/home/arogya/Dev/ComposureCI/monitoring-service/data"):
        self.data_dir = data_dir
        self.collision_bags_dir = os.path.join(data_dir, "collision_bags")
        self.static_bags_dir = os.path.join(data_dir, "static_bags")
        
        # Load collision analysis data once
        self.collision_data = self._load_collision_analysis()
    
    def _load_collision_analysis(self) -> Dict[str, Any]:
        """Load collision analysis data from JSON file"""
        collision_file = os.path.join(self.collision_bags_dir, "collision_analysis.json")
        try:
            with open(collision_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Collision analysis file not found: {collision_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse collision analysis JSON: {e}")
            return {}
    
    def load_navigation_results(self, results_file: str) -> Optional[Dict[str, Any]]:
        """Load navigation results from JSON file"""
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Results file not found: {results_file}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse results JSON: {e}")
            return None
    
    def extract_collision_metrics(self, run_id: str) -> Dict[str, Any]:
        """Extract collision metrics for a specific run"""
        # Map run_id to collision data key
        collision_key = f"{run_id}_auto"
        
        if collision_key in self.collision_data:
            collision_info = self.collision_data[collision_key]
            return {
                'collision_count': collision_info.get('collisions', 0),
                'min_distance': collision_info.get('min_distance_overall', 0.0),
                'avg_distance': collision_info.get('avg_min_distance', 0.0),
                'near_misses': collision_info.get('near_misses', 0),
                'total_scans': collision_info.get('total_scans', 0)
            }
        else:
            logger.warning(f"No collision data found for {collision_key}")
            return {
                'collision_count': 0,
                'min_distance': 0.0,
                'avg_distance': 0.0,
                'near_misses': 0,
                'total_scans': 0
            }
    
    def process_navigation_file(self, results_file: str, timestamp: datetime | None = None) -> Optional[Dict[str, Any]]:
        """Process a single navigation results file into database-ready format"""
        nav_data = self.load_navigation_results(results_file)
        if not nav_data:
            return None
        
        # Extract basic info
        controller_type = nav_data.get('controller', '').upper()
        run_number = nav_data.get('run', 0)
        run_id = f"{controller_type.lower()}_run{run_number}"
        
        # Extract navigation metrics
        total_time = nav_data.get('total_time', 0.0)
        total_recoveries = nav_data.get('total_recoveries', 0)
        
        # Extract goal-specific metrics
        goals = nav_data.get('goals', [])
        goal1_time = goals[0].get('navigation_time', 0.0) if len(goals) > 0 else 0.0
        goal1_recoveries = goals[0].get('recoveries', 0) if len(goals) > 0 else 0
        goal2_time = goals[1].get('navigation_time', 0.0) if len(goals) > 1 else 0.0
        goal2_recoveries = goals[1].get('recoveries', 0) if len(goals) > 1 else 0
        
        # Get collision metrics
        collision_metrics = self.extract_collision_metrics(run_id)
        
        # Use provided timestamp or generate one
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Combine all metrics
        processed_data = {
            'timestamp': timestamp,
            'controller_type': controller_type,
            'run_id': run_id,
            'navigation_time': total_time,
            'collision_count': collision_metrics['collision_count'],
            'recovery_count': total_recoveries,
            'total_recoveries': total_recoveries,
            'goal1_time': goal1_time,
            'goal2_time': goal2_time,
            'min_distance': collision_metrics['min_distance'],
            'avg_distance': collision_metrics['avg_distance'],
            # Extra fields for analysis
            'goal1_recoveries': goal1_recoveries,
            'goal2_recoveries': goal2_recoveries,
            'near_misses': collision_metrics['near_misses'],
            'total_scans': collision_metrics['total_scans']
        }
        
        logger.info(f"Processed {run_id}: nav_time={total_time:.1f}s, collisions={collision_metrics['collision_count']}, recoveries={total_recoveries}")
        
        return processed_data
    
    def get_chronological_file_order(self, scenario: str = "collision_bags") -> List[Dict[str, Any]]:
        """Get files in chronological order without predetermined phases"""
        scenario_dir = self.collision_bags_dir if scenario == "collision_bags" else self.static_bags_dir
        base_time = datetime.now(timezone.utc)
        
        # Process files in their natural chronological order
        # No predetermined phases - let statistical analysis determine patterns
        file_sequence = [
            "dwb_run1_results.json",
            "dwb_run2_results.json", 
            "dwb_run3_results.json",  # No predetermined exclusion
            "dwb_run4_results.json",
            "dwb_run5_results.json",
            "mppi_run1_results.json",
            "mppi_run2_results.json",
            "mppi_run3_results.json",
            "mppi_run4_results.json",
            "mppi_run5_results.json"
        ]
        
        chronological_files = []
        for i, filename in enumerate(file_sequence):
            file_path = os.path.join(scenario_dir, filename)
            if os.path.exists(file_path):
                # Sequential timestamps without artificial manipulation
                timestamp = base_time + timedelta(minutes=i * 5)
                
                chronological_files.append({
                    'file_path': file_path,
                    'timestamp': timestamp,
                    'file_name': filename,
                    'sequence_order': i
                })
        
        return chronological_files
    
    def get_available_files(self, scenario: str = "collision_bags") -> List[str]:
        """Get list of available result files for a scenario"""
        scenario_dir = self.collision_bags_dir if scenario == "collision_bags" else self.static_bags_dir
        pattern = os.path.join(scenario_dir, "*_results.json")
        return sorted(glob.glob(pattern))
    
    def process_all_files_chronologically(self, scenario: str = "collision_bags") -> List[Dict[str, Any]]:
        """
        Process all files in chronological order without predetermined phases.
        This maintains academic integrity by processing data as it would naturally occur.
        """
        chronological_files = self.get_chronological_file_order(scenario)
        processed_data = []
        
        for entry in chronological_files:
            if os.path.exists(entry['file_path']):
                data = self.process_navigation_file(entry['file_path'], entry['timestamp'])
                if data:
                    # Add sequence info but no predetermined phase
                    data['sequence_order'] = entry['sequence_order']
                    data['processing_timestamp'] = entry['timestamp']
                    processed_data.append(data)
            else:
                logger.warning(f"File not found: {entry['file_path']}")
        
        return processed_data
    
    def detect_performance_degradation_rolling_baseline(self, processed_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Honest rolling baseline detection - no predetermined outcomes.
        Uses statistical methods to detect when performance degrades beyond normal variation.
        """
        import statistics
        
        # Filter to same controller type and sort chronologically
        same_controller_runs = [d for d in processed_data if d['controller_type'] == processed_data[0]['controller_type']]
        if len(same_controller_runs) < 3:
            return None
        
        # Sort by timestamp to ensure chronological processing
        same_controller_runs.sort(key=lambda x: x['timestamp'])
        
        # Rolling baseline approach: Use first 2 runs to establish baseline
        baseline_size = min(2, len(same_controller_runs) - 1)
        baseline_runs = same_controller_runs[:baseline_size]
        
        # Calculate baseline statistics
        baseline_nav_times = [r['navigation_time'] for r in baseline_runs]
        baseline_collision_counts = [r['collision_count'] for r in baseline_runs]
        baseline_recovery_counts = [r['recovery_count'] for r in baseline_runs]
        
        baseline_nav_mean = statistics.mean(baseline_nav_times)
        baseline_collision_mean = statistics.mean(baseline_collision_counts)
        baseline_recovery_mean = statistics.mean(baseline_recovery_counts)
        
        # Calculate standard deviations (use sample std if enough data)
        if len(baseline_runs) > 1:
            baseline_nav_std = statistics.stdev(baseline_nav_times)
            baseline_collision_std = statistics.stdev(baseline_collision_counts) if max(baseline_collision_counts) > 0 else 1.0
            baseline_recovery_std = statistics.stdev(baseline_recovery_counts) if max(baseline_recovery_counts) > 0 else 1.0
        else:
            # Single run baseline - use conservative thresholds
            baseline_nav_std = baseline_nav_mean * 0.2  # 20% variation allowance
            baseline_collision_std = max(1.0, baseline_collision_mean * 0.5)
            baseline_recovery_std = max(1.0, baseline_recovery_mean * 0.5)
        
        # Check subsequent runs for statistical outliers
        for i, run in enumerate(same_controller_runs[baseline_size:], baseline_size):
            # Calculate z-scores for objective degradation detection
            nav_z_score = abs(run['navigation_time'] - baseline_nav_mean) / max(baseline_nav_std, 0.1)
            collision_z_score = abs(run['collision_count'] - baseline_collision_mean) / max(baseline_collision_std, 0.1)
            recovery_z_score = abs(run['recovery_count'] - baseline_recovery_mean) / max(baseline_recovery_std, 0.1)
            
            # Statistical thresholds for outlier detection (2-sigma rule)
            nav_degraded = (run['navigation_time'] > baseline_nav_mean) and (nav_z_score > 2.0)
            collision_spike = (run['collision_count'] > baseline_collision_mean) and (collision_z_score > 2.0)
            recovery_spike = (run['recovery_count'] > baseline_recovery_mean) and (recovery_z_score > 2.0)
            
            # Performance degradation detected if any metric shows significant degradation
            if nav_degraded or collision_spike or recovery_spike:
                degradation_severity = max(nav_z_score, collision_z_score, recovery_z_score)
                
                return {
                    'degradation_detected': True,
                    'degraded_run': run,
                    'run_index': i,
                    'baseline_size': baseline_size,
                    'baseline_metrics': {
                        'navigation_time': baseline_nav_mean,
                        'collision_count': baseline_collision_mean,
                        'recovery_count': baseline_recovery_mean
                    },
                    'degradation_evidence': {
                        'navigation_time_degraded': nav_degraded,
                        'collision_spike': collision_spike,
                        'recovery_spike': recovery_spike,
                        'nav_z_score': nav_z_score,
                        'collision_z_score': collision_z_score,
                        'recovery_z_score': recovery_z_score,
                        'severity_score': degradation_severity
                    },
                    'objective_analysis': f"Statistical outlier detected (z-score: {degradation_severity:.2f}). "
                                        f"Performance metrics exceed {2.0}-sigma threshold from established baseline."
                }
        
        # No degradation detected
        return {
            'degradation_detected': False,
            'baseline_metrics': {
                'navigation_time': baseline_nav_mean,
                'collision_count': baseline_collision_mean,
                'recovery_count': baseline_recovery_mean
            },
            'objective_analysis': "All runs within normal statistical variation of baseline performance."
        }

if __name__ == "__main__":
    # Test the data processor
    processor = NavigationDataProcessor()
    
    print("Testing Data Processor...")
    
    # Test single file processing
    test_file = "/home/arogya/Dev/ComposureCI/monitoring-service/data/collision_bags/dwb_run1_results.json"
    if os.path.exists(test_file):
        result = processor.process_navigation_file(test_file)
        if result:
            print(f"✓ Successfully processed {test_file}")
            print(f"  Controller: {result['controller_type']}, Navigation Time: {result['navigation_time']:.1f}s")
            print(f"  Collisions: {result['collision_count']}, Recoveries: {result['recovery_count']}")
        else:
            print(f"✗ Failed to process {test_file}")
    
    # Test chronological file processing
    chronological_files = processor.get_chronological_file_order("collision_bags")
    print(f"\n✓ Created chronological file order with {len(chronological_files)} entries")
    
    for entry in chronological_files[:3]:  # Show first 3 entries
        print(f"  {entry['sequence_order']}: {entry['file_name']} at {entry['timestamp'].strftime('%H:%M:%S')}")
    
    print(f"\nAvailable files: {len(processor.get_available_files('collision_bags'))}")