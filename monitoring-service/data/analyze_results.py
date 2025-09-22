#!/usr/bin/env python3

import json
import glob
import numpy as np
import sys
from scipy import stats

class NavigationAnalyzer:
    def __init__(self):
        self.dwb_results = []
        self.mppi_results = []
    
    def load_results(self, pattern="*_results.json"):
        """Load all result files"""
        files = glob.glob(pattern)
        
        for file in files:
            with open(file, 'r') as f:
                data = json.load(f)
                
            if data['controller'] == 'dwb':
                self.dwb_results.append(data)
            elif data['controller'] == 'mppi':
                self.mppi_results.append(data)
        
        print(f"Loaded {len(self.dwb_results)} DWB runs and {len(self.mppi_results)} MPPI runs")
    
    def extract_metrics(self, results):
        """Extract key metrics from results"""
        metrics = {
            'total_times': [],
            'total_recoveries': [],
            'goal1_times': [],
            'goal2_times': [],
            'goal1_recoveries': [],
            'goal2_recoveries': []
        }
        
        for result in results:
            metrics['total_times'].append(result['total_time'])
            metrics['total_recoveries'].append(result['total_recoveries'])
            
            if len(result['goals']) >= 2:
                metrics['goal1_times'].append(result['goals'][0]['navigation_time'])
                metrics['goal2_times'].append(result['goals'][1]['navigation_time'])
                metrics['goal1_recoveries'].append(result['goals'][0]['recoveries'])
                metrics['goal2_recoveries'].append(result['goals'][1]['recoveries'])
        
        return metrics
    
    def calculate_statistics(self, data):
        """Calculate mean, std, confidence interval"""
        if not data:
            return {'mean': 0, 'std': 0, 'count': 0, 'ci_low': 0, 'ci_high': 0}
            
        mean = np.mean(data)
        std = np.std(data, ddof=1) if len(data) > 1 else 0
        count = len(data)
        
        # 95% confidence interval
        if count > 1:
            ci = stats.t.interval(0.95, count-1, loc=mean, scale=stats.sem(data))
            ci_low, ci_high = ci
        else:
            ci_low = ci_high = mean
            
        return {
            'mean': mean,
            'std': std, 
            'count': count,
            'ci_low': ci_low,
            'ci_high': ci_high
        }
    
    def perform_t_test(self, data1, data2, metric_name):
        """Perform independent t-test between two datasets"""
        if len(data1) < 2 or len(data2) < 2:
            return None
            
        t_stat, p_value = stats.ttest_ind(data1, data2)
        
        result = {
            'metric': metric_name,
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'effect_size': (np.mean(data1) - np.mean(data2)) / np.sqrt((np.var(data1) + np.var(data2)) / 2)
        }
        
        return result
    
    def generate_report(self):
        """Generate comprehensive comparison report"""
        if not self.dwb_results or not self.mppi_results:
            print("ERROR: Need results from both controllers!")
            return
            
        dwb_metrics = self.extract_metrics(self.dwb_results)
        mppi_metrics = self.extract_metrics(self.mppi_results)
        
        print("=" * 60)
        print("NAVIGATION CONTROLLER COMPARISON REPORT")
        print("=" * 60)
        
        # Total navigation time comparison
        print("\n1. TOTAL NAVIGATION TIME (seconds)")
        print("-" * 40)
        
        dwb_total = self.calculate_statistics(dwb_metrics['total_times'])
        mppi_total = self.calculate_statistics(mppi_metrics['total_times'])
        
        print(f"DWB:  {dwb_total['mean']:.2f} ± {dwb_total['std']:.2f} (n={dwb_total['count']})")
        print(f"MPPI: {mppi_total['mean']:.2f} ± {mppi_total['std']:.2f} (n={mppi_total['count']})")
        
        improvement = ((dwb_total['mean'] - mppi_total['mean']) / dwb_total['mean']) * 100
        print(f"Improvement: {improvement:.1f}% {'faster' if improvement > 0 else 'slower'}")
        
        # Statistical test
        t_test = self.perform_t_test(dwb_metrics['total_times'], mppi_metrics['total_times'], 'Total Time')
        if t_test:
            print(f"Statistical significance: p = {t_test['p_value']:.4f} ({'significant' if t_test['significant'] else 'not significant'})")
        
        # Recovery behavior comparison
        print("\n2. RECOVERY BEHAVIORS")
        print("-" * 40)
        
        dwb_recovery = self.calculate_statistics(dwb_metrics['total_recoveries'])
        mppi_recovery = self.calculate_statistics(mppi_metrics['total_recoveries'])
        
        print(f"DWB:  {dwb_recovery['mean']:.1f} ± {dwb_recovery['std']:.1f} recoveries")
        print(f"MPPI: {mppi_recovery['mean']:.1f} ± {mppi_recovery['std']:.1f} recoveries")
        
        # Segment analysis
        print("\n3. SEGMENT ANALYSIS")
        print("-" * 40)
        
        dwb_seg1 = self.calculate_statistics(dwb_metrics['goal1_times'])
        mppi_seg1 = self.calculate_statistics(mppi_metrics['goal1_times'])
        dwb_seg2 = self.calculate_statistics(dwb_metrics['goal2_times'])
        mppi_seg2 = self.calculate_statistics(mppi_metrics['goal2_times'])
        
        print(f"Bottom→Top: DWB {dwb_seg1['mean']:.2f}s vs MPPI {mppi_seg1['mean']:.2f}s")
        print(f"Top→Bottom: DWB {dwb_seg2['mean']:.2f}s vs MPPI {mppi_seg2['mean']:.2f}s")
        
        # Summary and recommendation
        print("\n4. SUMMARY & RECOMMENDATION")
        print("-" * 40)
        
        if t_test and t_test['significant']:
            if improvement > 0:
                print(f"✓ MPPI shows statistically significant {improvement:.1f}% improvement")
                print("  Recommendation: Use MPPI for dynamic environments")
            else:
                print(f"✓ DWB shows statistically significant {abs(improvement):.1f}% improvement") 
                print("  Recommendation: Use DWB for this scenario")
        else:
            print("⚠ No statistically significant difference found")
            print("  Recommendation: Either controller acceptable, consider other factors")
        
        print(f"\nEffect size: {t_test['effect_size']:.2f}" if t_test else "")
        
        # Add collision analysis note
        print("\n5. COLLISION ANALYSIS")
        print("-" * 40)
        print("For collision analysis, run:")
        print("python3 collision_analyzer.py")
        
        print("=" * 60)
    
    def export_csv(self, filename="navigation_results.csv"):
        """Export results to CSV for further analysis"""
        import csv
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Controller', 'Run', 'Total_Time', 'Total_Recoveries', 
                           'Goal1_Time', 'Goal1_Recoveries', 'Goal2_Time', 'Goal2_Recoveries'])
            
            for result in self.dwb_results:
                row = ['DWB', result['run'], result['total_time'], result['total_recoveries']]
                if len(result['goals']) >= 2:
                    row.extend([result['goals'][0]['navigation_time'], result['goals'][0]['recoveries'],
                              result['goals'][1]['navigation_time'], result['goals'][1]['recoveries']])
                writer.writerow(row)
            
            for result in self.mppi_results:
                row = ['MPPI', result['run'], result['total_time'], result['total_recoveries']]
                if len(result['goals']) >= 2:
                    row.extend([result['goals'][0]['navigation_time'], result['goals'][0]['recoveries'],
                              result['goals'][1]['navigation_time'], result['goals'][1]['recoveries']])
                writer.writerow(row)
        
        print(f"Results exported to {filename}")

def main():
    analyzer = NavigationAnalyzer()
    analyzer.load_results()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--csv':
        analyzer.export_csv()
    else:
        analyzer.generate_report()

if __name__ == '__main__':
    main()