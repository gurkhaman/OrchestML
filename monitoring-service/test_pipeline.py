#!/usr/bin/env python3
"""
Quick test script to verify all components work without dependencies
"""

import os
import json
from datetime import datetime

def test_data_availability():
    """Test that all required data files exist"""
    print("🔍 Testing data availability...")
    
    base_dir = "/home/arogya/Dev/ComposureCI/monitoring-service/data/collision_bags"
    required_files = [
        "dwb_run1_results.json",
        "dwb_run2_results.json", 
        "dwb_run3_results.json",
        "dwb_run4_results.json",
        "dwb_run5_results.json",
        "mppi_run1_results.json",
        "mppi_run2_results.json",
        "mppi_run3_results.json",
        "mppi_run4_results.json",
        "mppi_run5_results.json",
        "collision_analysis.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files found")
        return True

def test_data_processing():
    """Test data processing without database"""
    print("\n🔍 Testing data processing...")
    
    try:
        from data_processor import NavigationDataProcessor  # type: ignore
        
        processor = NavigationDataProcessor()
        
        # Test single file
        test_file = "/home/arogya/Dev/ComposureCI/monitoring-service/data/collision_bags/dwb_run3_results.json"
        result = processor.process_navigation_file(test_file)
        
        if result:
            print(f"  ✓ Successfully processed {os.path.basename(test_file)}")
            print(f"    Navigation time: {result['navigation_time']:.1f}s")
            print(f"    Collisions: {result['collision_count']}")
            print(f"    Recoveries: {result['recovery_count']}")
            
            # Check if this is the degraded run
            if result['navigation_time'] > 200:
                print(f"    🚨 DEGRADATION DETECTED: {result['navigation_time']:.1f}s > 200s threshold")
            
            return True
        else:
            print(f"  ✗ Failed to process {test_file}")
            return False
            
    except Exception as e:
        print(f"  ✗ Data processing test failed: {e}")
        return False

def test_timeline_creation():
    """Test timeline creation for simulation"""
    print("\n🔍 Testing timeline creation...")
    
    try:
        from data_processor import NavigationDataProcessor  # type: ignore
        
        processor = NavigationDataProcessor()
        timeline = processor.create_simulation_timeline("collision_bags")
        
        print(f"  ✓ Created timeline with {len(timeline)} entries")
        
        # Show key phases
        phases = {}
        for entry in timeline:
            phase = entry['phase']
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(entry['file_name'])
        
        for phase, files in phases.items():
            print(f"    {phase}: {len(files)} files")
        
        # Find degradation point
        degradation_entries = [e for e in timeline if e['phase'] == 'degradation']
        if degradation_entries:
            print(f"    🎯 Degradation trigger: {degradation_entries[0]['file_name']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Timeline creation test failed: {e}")
        return False

def test_mock_orchestrator():
    """Test mock orchestrator"""
    print("\n🔍 Testing mock orchestrator...")
    
    try:
        from mock_orchestrator import MockOrchestrator  # type: ignore
        
        orchestrator = MockOrchestrator()
        
        # Test trigger
        test_trigger = {
            "trigger_type": "performance_degradation",
            "current_controller": "DWB",
            "reason": "Navigation time exceeded threshold",
            "metrics": {
                "navigation_time": 216.58,
                "collision_count": 101,
                "recovery_count": 10
            }
        }
        
        response = orchestrator.receive_trigger(test_trigger)
        
        if response['action'] == 'recompose' and response['new_controller'] == 'MPPI':
            print(f"  ✓ Mock orchestrator working correctly")
            print(f"    Response: {response['message']}")
            return True
        else:
            print(f"  ✗ Unexpected orchestrator response: {response}")
            return False
            
    except Exception as e:
        print(f"  ✗ Mock orchestrator test failed: {e}")
        return False

def test_expected_improvement():
    """Test that we can calculate the expected improvement"""
    print("\n🔍 Testing performance improvement calculation...")
    
    try:
        from data_processor import NavigationDataProcessor  # type: ignore
        
        processor = NavigationDataProcessor()
        
        # Get DWB baseline (runs 1,2,4,5)
        dwb_files = [
            "dwb_run1_results.json",
            "dwb_run2_results.json", 
            "dwb_run4_results.json",
            "dwb_run5_results.json"
        ]
        
        dwb_times = []
        for file in dwb_files:
            file_path = f"/home/arogya/Dev/ComposureCI/monitoring-service/data/collision_bags/{file}"
            result = processor.process_navigation_file(file_path)
            if result:
                dwb_times.append(result['navigation_time'])
        
        # Get MPPI performance
        mppi_files = [
            "mppi_run1_results.json",
            "mppi_run2_results.json",
            "mppi_run3_results.json", 
            "mppi_run4_results.json",
            "mppi_run5_results.json"
        ]
        
        mppi_times = []
        for file in mppi_files:
            file_path = f"/home/arogya/Dev/ComposureCI/monitoring-service/data/collision_bags/{file}"
            result = processor.process_navigation_file(file_path)
            if result:
                mppi_times.append(result['navigation_time'])
        
        if dwb_times and mppi_times:
            dwb_avg = sum(dwb_times) / len(dwb_times)
            mppi_avg = sum(mppi_times) / len(mppi_times)
            improvement = ((dwb_avg - mppi_avg) / dwb_avg) * 100
            
            print(f"  ✓ Performance calculation successful")
            print(f"    DWB baseline: {dwb_avg:.1f}s (from {len(dwb_times)} runs)")
            print(f"    MPPI average: {mppi_avg:.1f}s (from {len(mppi_times)} runs)")
            print(f"    Improvement: {improvement:.1f}%")
            
            if improvement > 15:  # Expecting ~19% improvement
                print(f"    🎉 Significant improvement achieved!")
                return True
            else:
                print(f"    ⚠️  Improvement less than expected")
                return False
        else:
            print(f"  ✗ Could not calculate performance metrics")
            return False
            
    except Exception as e:
        print(f"  ✗ Performance calculation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPOSURECI MONITORING PIPELINE TEST")
    print("=" * 60)
    
    tests = [
        ("Data Availability", test_data_availability),
        ("Data Processing", test_data_processing), 
        ("Timeline Creation", test_timeline_creation),
        ("Mock Orchestrator", test_mock_orchestrator),
        ("Performance Improvement", test_expected_improvement)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to run with dependencies.")
        print("\nNext steps:")
        print("1. Run: uv add psycopg2-binary requests")
        print("2. Run: python3 monitoring_pipeline.py")
        print("3. Check DataGrip for results")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check errors above.")

if __name__ == "__main__":
    main()