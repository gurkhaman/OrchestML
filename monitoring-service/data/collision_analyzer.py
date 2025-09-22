#!/usr/bin/env python3

import sqlite3
import numpy as np
import json
import sys
import pickle
import glob
from pathlib import Path

class CollisionAnalyzer:
    def __init__(self, collision_threshold=0.3, near_miss_threshold=0.5):
        self.collision_threshold = collision_threshold  # meters
        self.near_miss_threshold = near_miss_threshold  # meters
        
    def analyze_bag_collisions(self, bag_path):
        """Analyze collision events from a bag file"""
        db_path = Path(bag_path) / f"{Path(bag_path).name}_0.db3"
        
        if not db_path.exists():
            print(f"Database file not found: {db_path}")
            return None
            
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get laser scan data
        cursor.execute("""
            SELECT timestamp, data 
            FROM messages m
            JOIN topics t ON m.topic_id = t.id
            WHERE t.name = '/scan'
            ORDER BY timestamp
        """)
        
        scan_data = cursor.fetchall()
        conn.close()
        
        if not scan_data:
            print("No laser scan data found")
            return None
            
        collisions = []
        near_misses = []
        min_distances = []
        
        for timestamp, data_blob in scan_data:
            try:
                # Deserialize ROS message (simplified approach)
                ranges = self.extract_ranges_from_blob(data_blob)
                if ranges is None:
                    continue
                    
                # Filter out invalid readings (inf, nan)
                valid_ranges = [r for r in ranges if 0.01 < r < 10.0]
                
                if not valid_ranges:
                    continue
                    
                min_dist = min(valid_ranges)
                min_distances.append(min_dist)
                
                # Check for collision
                if min_dist < self.collision_threshold:
                    collisions.append({
                        'timestamp': timestamp,
                        'distance': min_dist,
                        'type': 'collision'
                    })
                # Check for near miss
                elif min_dist < self.near_miss_threshold:
                    near_misses.append({
                        'timestamp': timestamp,
                        'distance': min_dist,
                        'type': 'near_miss'
                    })
                    
            except Exception as e:
                continue
                
        return {
            'collisions': len(collisions),
            'near_misses': len(near_misses),
            'min_distance_overall': min(min_distances) if min_distances else float('inf'),
            'avg_min_distance': np.mean(min_distances) if min_distances else float('inf'),
            'collision_events': collisions,
            'near_miss_events': near_misses,
            'total_scans': len(scan_data)
        }
    
    def extract_ranges_from_blob(self, data_blob):
        """Extract range data from ROS message blob (simplified)"""
        try:
            # This is a simplified approach - in reality, you'd need proper ROS deserialization
            # For now, we'll use a heuristic approach
            
            # Skip ROS message header and extract float array
            # This is approximate and may need adjustment based on your specific setup
            data_start = 100  # Skip headers
            if len(data_blob) < data_start + 360 * 4:  # Assuming ~360 readings, 4 bytes each
                return None
                
            # Extract as little-endian floats
            ranges = []
            for i in range(data_start, min(len(data_blob) - 4, data_start + 360 * 4), 4):
                try:
                    # Unpack 4 bytes as little-endian float
                    range_val = np.frombuffer(data_blob[i:i+4], dtype=np.float32)[0]
                    ranges.append(range_val)
                except:
                    continue
                    
            return ranges if ranges else None
            
        except Exception as e:
            return None
    
    def analyze_all_bags(self, pattern="*_run*_auto"):
        """Analyze all bag files matching pattern"""
        bag_dirs = glob.glob(pattern)
        results = {}
        
        for bag_dir in bag_dirs:
            if Path(bag_dir).is_dir():
                print(f"Analyzing {bag_dir}...")
                collision_data = self.analyze_bag_collisions(bag_dir)
                if collision_data:
                    results[bag_dir] = collision_data
                    
        return results
    
    def generate_collision_report(self, results):
        """Generate collision analysis report"""
        if not results:
            print("No collision data available")
            return
            
        print("=" * 60)
        print("COLLISION ANALYSIS REPORT")
        print("=" * 60)
        
        dwb_results = {k: v for k, v in results.items() if 'dwb' in k}
        mppi_results = {k: v for k, v in results.items() if 'mppi' in k}
        
        def summarize_controller(controller_results, name):
            if not controller_results:
                return
                
            collisions = [r['collisions'] for r in controller_results.values()]
            near_misses = [r['near_misses'] for r in controller_results.values()]
            min_dists = [r['min_distance_overall'] for r in controller_results.values()]
            avg_dists = [r['avg_min_distance'] for r in controller_results.values()]
            
            print(f"\n{name} CONTROLLER:")
            print(f"  Collision Events: {np.mean(collisions):.1f} ± {np.std(collisions):.1f}")
            print(f"  Near Miss Events: {np.mean(near_misses):.1f} ± {np.std(near_misses):.1f}")
            print(f"  Minimum Distance: {np.mean(min_dists):.3f} ± {np.std(min_dists):.3f} m")
            print(f"  Average Min Distance: {np.mean(avg_dists):.3f} ± {np.std(avg_dists):.3f} m")
            
            return {
                'collisions': collisions,
                'near_misses': near_misses,
                'min_distances': min_dists,
                'avg_distances': avg_dists
            }
        
        dwb_summary = summarize_controller(dwb_results, "DWB")
        mppi_summary = summarize_controller(mppi_results, "MPPI")
        
        # Comparison
        if dwb_summary and mppi_summary:
            print(f"\nCOMPARISON:")
            dwb_total_collisions = sum(dwb_summary['collisions'])
            mppi_total_collisions = sum(mppi_summary['collisions'])
            
            print(f"  Total Collisions: DWB={dwb_total_collisions}, MPPI={mppi_total_collisions}")
            
            if dwb_total_collisions == 0 and mppi_total_collisions == 0:
                print("  ✓ Both controllers avoided collisions")
            elif mppi_total_collisions < dwb_total_collisions:
                print("  ✓ MPPI had fewer collisions")
            elif dwb_total_collisions < mppi_total_collisions:
                print("  ✓ DWB had fewer collisions")
            else:
                print("  = Equal collision performance")
        
        print("=" * 60)
    
    def save_collision_data(self, results, filename="collision_analysis.json"):
        """Save collision analysis to JSON"""
        # Convert numpy types to native Python for JSON serialization
        json_results = {}
        for bag, data in results.items():
            json_results[bag] = {
                'collisions': int(data['collisions']),
                'near_misses': int(data['near_misses']),
                'min_distance_overall': float(data['min_distance_overall']),
                'avg_min_distance': float(data['avg_min_distance']),
                'total_scans': int(data['total_scans'])
            }
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        print(f"Collision data saved to {filename}")

def main():
    analyzer = CollisionAnalyzer(
        collision_threshold=0.3,  # 30cm = collision
        near_miss_threshold=0.5   # 50cm = near miss
    )
    
    print("Analyzing collision data from bag files...")
    results = analyzer.analyze_all_bags()
    
    if results:
        analyzer.generate_collision_report(results)
        analyzer.save_collision_data(results)
    else:
        print("No bag files found or no collision data available")
        print("Make sure you have bag files in the current directory matching pattern '*_run*_auto'")

if __name__ == '__main__':
    main()