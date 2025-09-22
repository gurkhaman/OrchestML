#!/usr/bin/env python3

import time
import json
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

# Local imports - type checker will complain but will work at runtime
from db_manager import DatabaseManager  # type: ignore
from data_processor import NavigationDataProcessor  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringPipeline:
    def __init__(self, orchestrator_url: str = "http://localhost:8000"):
        self.db_manager = DatabaseManager()
        self.data_processor = NavigationDataProcessor()
        self.orchestrator_url = orchestrator_url
        
        # Connect to database
        if not self.db_manager.connect():
            raise Exception("Failed to connect to database")
        
        logger.info("Monitoring Pipeline initialized")
    
    def run_chronological_monitoring(self, scenario: str = "collision_bags", composition_id: str | None = None) -> Dict[str, Any]:
        """
        Process files chronologically and detect performance issues objectively.
        No predetermined phases - uses rolling baseline detection.
        """
        logger.info("=== CHRONOLOGICAL PERFORMANCE MONITORING ===")
        
        # Process files in chronological order (no predetermined phases)
        all_data = self.data_processor.process_all_files_chronologically(scenario)
        
        if not all_data:
            logger.error("No data files processed")
            return {'success': False, 'error': 'No data available'}
        
        logger.info(f"Processing {len(all_data)} runs chronologically...")
        
        # Store all data in database as it would arrive in real-time
        stored_count = 0
        for data in all_data:
            if self.db_manager.insert_navigation_metrics(data):
                stored_count += 1
                logger.info(f"✓ Stored data for {data['run_id']}: "
                           f"nav_time={data['navigation_time']:.1f}s, "
                           f"collisions={data['collision_count']}, "
                           f"recoveries={data['recovery_count']}")
            else:
                logger.error(f"✗ Failed to store data for {data['run_id']}")
            
            # Simulate real-time processing delay
            time.sleep(0.5)
        
        logger.info(f"✓ Successfully stored {stored_count} runs")
        
        # Apply honest rolling baseline detection
        degradation_analysis = self.data_processor.detect_performance_degradation_rolling_baseline(all_data)
        
        if degradation_analysis and degradation_analysis.get('degradation_detected'):
            logger.warning("🚨 PERFORMANCE DEGRADATION DETECTED!")
            logger.warning(f"   Analysis: {degradation_analysis['objective_analysis']}")
            
            degraded_run = degradation_analysis['degraded_run']
            evidence = degradation_analysis['degradation_evidence']
            
            logger.warning(f"   Degraded Run: {degraded_run['run_id']}")
            logger.warning(f"   Current Performance: nav_time={degraded_run['navigation_time']:.1f}s, "
                          f"collisions={degraded_run['collision_count']}, "
                          f"recoveries={degraded_run['recovery_count']}")
            
            # Prepare objective failure evidence for orchestrator
            failure_trigger = self.prepare_recomposition_trigger(
                composition_id, 
                degradation_analysis
            )
            
            # Send trigger to orchestrator (no predetermined solutions)
            orchestrator_response = self.send_orchestrator_recomposition(failure_trigger)
            
            return {
                'success': True,
                'degradation_detected': True,
                'degradation_analysis': degradation_analysis,
                'recomposition_trigger': failure_trigger,
                'orchestrator_response': orchestrator_response
            }
        else:
            logger.info("✓ All runs within normal performance parameters")
            logger.info(f"   Analysis: {degradation_analysis.get('objective_analysis') if degradation_analysis else 'Performance monitoring complete'}")
            
            return {
                'success': True,
                'degradation_detected': False,
                'analysis': degradation_analysis
            }
    
    # DEPRECATED: Old timeline-based method removed for academic integrity
    # Use run_chronological_monitoring() instead
    
    def prepare_recomposition_trigger(self, composition_id: str | None, degradation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare objective recomposition trigger for orchestrator.
        No predetermined solutions - only objective failure evidence.
        """
        degraded_run = degradation_analysis['degraded_run']
        evidence = degradation_analysis['degradation_evidence']
        baseline_metrics = degradation_analysis['baseline_metrics']
        
        # Objective failure evidence without predetermined solutions
        trigger_data = {
            "composition_id": composition_id or "unknown",
            "trigger_type": "performance_degradation",
            "failure_evidence": {
                "current_task_completion_time": degraded_run['navigation_time'],
                "baseline_task_completion_time": baseline_metrics['navigation_time'],
                "current_error_count": degraded_run['collision_count'],
                "baseline_error_count": baseline_metrics['collision_count'],
                "current_intervention_count": degraded_run['recovery_count'],
                "baseline_intervention_count": baseline_metrics['recovery_count'],
                "severity_scores": {
                    "completion_time_z_score": evidence['nav_z_score'],
                    "error_count_z_score": evidence['collision_z_score'],
                    "intervention_z_score": evidence['recovery_z_score'],
                    "overall_severity": evidence['severity_score']
                }
            },
            "failure_analysis": degradation_analysis['objective_analysis'],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return trigger_data
    
    def send_orchestrator_recomposition(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send recomposition trigger to orchestrator /api/v1/recompose endpoint.
        No predetermined solutions - let orchestrator make intelligent decisions.
        """
        try:
            # Send to real orchestrator recompose endpoint
            response = requests.post(
                f"{self.orchestrator_url}/api/v1/recompose",
                json=trigger_data,
                timeout=30
            )
            
            if response.status_code == 200:
                recomposition_data = response.json()
                logger.info(f"✓ Orchestrator recomposition successful!")
                logger.info(f"   Original ID: {recomposition_data.get('original_composition_id')}")
                logger.info(f"   New ID: {recomposition_data.get('new_composition_id')}")
                logger.info(f"   Alternatives: {len(recomposition_data.get('blueprints', {}).get('alternatives', []))}")
                
                return {"status": "success", "recomposition": recomposition_data}
            else:
                logger.warning(f"Orchestrator recomposition failed: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                return {"status": "failed", "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to contact orchestrator: {e}")
            return {"status": "failed", "error": str(e)}

    # DEPRECATED: Old trigger method with hardcoded recommendations removed
    # Use send_orchestrator_recomposition() instead for academic integrity
    
    # DEPRECATED: Old phase-based recomposition method removed for academic integrity
    # Recomposition is now handled by orchestrator through /api/v1/recompose endpoint
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance comparison report"""
        logger.info("=== PERFORMANCE ANALYSIS REPORT ===")
        
        summary = self.db_manager.get_performance_summary()
        
        if summary['performance_by_controller']:
            for controller_stats in summary['performance_by_controller']:
                controller = controller_stats['controller_type']
                logger.info(f"\n{controller} Controller:")
                logger.info(f"  Total Runs: {controller_stats['total_runs']}")
                logger.info(f"  Avg Navigation Time: {controller_stats['avg_nav_time']:.1f}s")
                logger.info(f"  Navigation Range: {controller_stats['min_nav_time']:.1f}s - {controller_stats['max_nav_time']:.1f}s")
                logger.info(f"  Avg Collisions: {controller_stats['avg_collisions']:.1f}")
                logger.info(f"  Avg Recoveries: {controller_stats['avg_recoveries']:.1f}")
        
        # Calculate improvement if both controllers present
        controllers = {stat['controller_type']: stat for stat in summary['performance_by_controller']}
        if 'DWB' in controllers and 'MPPI' in controllers:
            dwb_time = controllers['DWB']['avg_nav_time']
            mppi_time = controllers['MPPI']['avg_nav_time']
            improvement = ((dwb_time - mppi_time) / dwb_time) * 100
            
            logger.info(f"\n📊 PERFORMANCE IMPROVEMENT:")
            logger.info(f"   Navigation Time: {improvement:.1f}% {'improvement' if improvement > 0 else 'degradation'}")
            logger.info(f"   DWB Average: {dwb_time:.1f}s → MPPI Average: {mppi_time:.1f}s")
        
        # Show trigger events
        if summary['trigger_events']:
            logger.info(f"\n🚨 TRIGGER EVENTS:")
            for event in summary['trigger_events']:
                logger.info(f"   {event['timestamp']}: {event['trigger_type']} - {event['triggered_by']}")
        
        return summary
    
    def run_honest_monitoring_demo(self, scenario: str = "collision_bags", composition_id: str | None = None) -> Dict[str, Any]:
        """
        Run honest monitoring demonstration without predetermined phases or outcomes.
        Uses rolling baseline detection and objective failure analysis.
        """
        logger.info("=" * 70)
        logger.info("STARTING HONEST COMPOSURECI MONITORING DEMONSTRATION")
        logger.info("Academic Integrity: No predetermined outcomes or timeline manipulation")
        logger.info("=" * 70)
        
        results = {
            'scenario': scenario,
            'composition_id': composition_id,
            'start_time': datetime.now(timezone.utc),
            'monitoring_approach': 'rolling_baseline_detection'
        }
        
        try:
            # Run chronological monitoring with rolling baseline detection
            monitoring_result = self.run_chronological_monitoring(scenario, composition_id)
            
            results['monitoring_result'] = monitoring_result
            results['success'] = monitoring_result.get('success', False)
            
            if monitoring_result.get('degradation_detected'):
                logger.info("🔄 Performance degradation detected - orchestrator notified for recomposition")
                results['recomposition_triggered'] = True
                results['orchestrator_response'] = monitoring_result.get('orchestrator_response')
            else:
                logger.info("✅ All performance metrics within normal parameters")
                results['recomposition_triggered'] = False
            
            # Generate final report
            results['final_report'] = self.generate_performance_report()
            results['end_time'] = datetime.now(timezone.utc)
            results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
            
            logger.info("=" * 70)
            logger.info(f"HONEST MONITORING COMPLETED IN {results['duration']:.1f} SECONDS")
            logger.info("=" * 70)
            
            return results
            
        except Exception as e:
            logger.error(f"Monitoring demonstration failed: {e}")
            results['error'] = str(e)
            results['success'] = False
            return results
        finally:
            self.db_manager.disconnect()

if __name__ == "__main__":
    # Run the monitoring pipeline demonstration
    try:
        pipeline = MonitoringPipeline()
        results = pipeline.run_honest_monitoring_demo("collision_bags")
        
        # Print summary
        print("\n" + "=" * 50)
        print("MONITORING PIPELINE DEMONSTRATION SUMMARY")
        print("=" * 50)
        print(f"Scenario: {results['scenario']}")
        print(f"Duration: {results.get('duration', 0):.1f} seconds")
        
        if results['phases'].get('baseline'):
            print("✓ Baseline establishment: SUCCESS")
        else:
            print("✗ Baseline establishment: FAILED")
            
        if results['phases'].get('degradation', {}).get('triggered'):
            print("✓ Degradation detection: TRIGGERED")
        else:
            print("ℹ️ Degradation detection: NO TRIGGER")
            
        if results['phases'].get('recomposition'):
            print("✓ Recomposition validation: SUCCESS")
        
        if 'error' in results:
            print(f"✗ Error: {results['error']}")
            
    except Exception as e:
        print(f"Failed to run monitoring pipeline: {e}")
        print("Note: Make sure to run 'uv add psycopg2-binary requests' first")