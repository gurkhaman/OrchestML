#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
import time
import json
import sys
import subprocess
import os

class NavigationExperiment(Node):
    def __init__(self, controller_name, run_number):
        super().__init__('navigation_experiment')
        self.controller_name = controller_name
        self.run_number = run_number
        
        # Action client for navigation
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Navigation goals (bottom to top to bottom)
        self.goals = [
            {'x': 5.5, 'y': 1.0, 'z': 0.0, 'w': -1.0},  # Top of map
            {'x': -1.1, 'y': 1.5, 'z': 0.0, 'w': 1.0}  # Bottom of map 
        ]
        
        # Reset position (initial spawn location)
        self.reset_position = {'x': -2.0, 'y': -0.5, 'z': 0.0, 'w': 1.0}
        
        # Results storage
        self.results = {
            'controller': controller_name,
            'run': run_number,
            'goals': [],
            'total_time': 0.0,
            'total_recoveries': 0
        }
        
        # Bag recording process
        self.bag_process = None

    def start_bag_recording(self):
        """Start recording rosbag"""
        bag_name = f"{self.controller_name}_run{self.run_number}_auto"
        cmd = [
            'ros2', 'bag', 'record', '-o', bag_name,
            '/navigate_to_pose/_action/feedback',
            '/navigate_to_pose/_action/result', 
            '/amcl_pose', '/cmd_vel', '/scan', '/odom'
        ]
        
        self.bag_process = subprocess.Popen(cmd)
        time.sleep(2)  # Give bag time to start
        self.get_logger().info(f"Started recording bag: {bag_name}")

    def stop_bag_recording(self):
        """Stop recording rosbag"""
        if self.bag_process:
            self.bag_process.terminate()
            self.bag_process.wait()
            self.get_logger().info("Stopped bag recording")
            self.bag_process = None  # Prevent duplicate stops

    def create_goal_pose(self, x, y, z, w):
        """Create a NavigateToPose goal"""
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = "map"
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = z
        goal_msg.pose.pose.orientation.w = w
        return goal_msg

    def send_goal(self, goal_dict):
        """Send navigation goal and wait for result"""
        self.get_logger().info(f"Sending goal: {goal_dict}")
        
        # Wait for action server
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("Action server not available!")
            return None
            
        goal_msg = self.create_goal_pose(
            goal_dict['x'], goal_dict['y'], 
            goal_dict['z'], goal_dict['w']
        )
        
        # Send goal and get future
        start_time = time.time()
        send_goal_future = self._action_client.send_goal_async(
            goal_msg, 
            feedback_callback=self.feedback_callback
        )
        
        rclpy.spin_until_future_complete(self, send_goal_future)
        goal_handle = send_goal_future.result()
        
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error("Goal rejected!")
            return None
            
        # Wait for result
        get_result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, get_result_future)
        
        end_time = time.time()
        result = get_result_future.result().result
        
        # Extract result code safely
        try:
            result_code = int(result.result) if hasattr(result, 'result') else 0
        except:
            result_code = 0  # Default to success
        
        goal_data = {
            'goal': goal_dict,
            'navigation_time': end_time - start_time,
            'result_code': result_code,
            'recoveries': self.current_recoveries
        }
        
        self.get_logger().info(f"Goal completed in {goal_data['navigation_time']:.2f}s with {self.current_recoveries} recoveries")
        return goal_data

    def feedback_callback(self, feedback_msg):
        """Handle navigation feedback"""
        feedback = feedback_msg.feedback
        self.current_recoveries = feedback.number_of_recoveries

    def run_experiment(self):
        """Run the complete navigation experiment"""
        self.get_logger().info(f"Starting experiment: {self.controller_name} Run {self.run_number}")
        
        # Start bag recording
        self.start_bag_recording()
        
        # Wait for robot to settle
        time.sleep(3)
        
        total_start = time.time()
        
        # Execute all goals
        for i, goal in enumerate(self.goals):
            self.current_recoveries = 0
            
            goal_result = self.send_goal(goal)
            if goal_result:
                self.results['goals'].append(goal_result)
                self.results['total_recoveries'] += goal_result['recoveries']
            else:
                self.get_logger().error(f"Failed to complete goal {i+1}")
                break
                
            # Brief pause between goals
            time.sleep(2)
        
        total_end = time.time()
        self.results['total_time'] = total_end - total_start
        
        # Stop recording after waypoints are completed
        self.stop_bag_recording()
        
        # Reset robot to initial position
        self.get_logger().info("Resetting robot to initial position...")
        self.current_recoveries = 0
        reset_result = self.send_goal(self.reset_position)
        if reset_result:
            self.get_logger().info("Reset completed successfully")
        else:
            self.get_logger().warning("Reset failed")
        
        # Save results
        self.save_results()
        
        self.get_logger().info(f"Experiment completed in {self.results['total_time']:.2f}s")

    def save_results(self):
        """Save experiment results to JSON"""
        filename = f"{self.controller_name}_run{self.run_number}_results.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        self.get_logger().info(f"Results saved to {filename}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 run_nav_experiment.py <controller_name> <run_number>")
        print("Example: python3 run_nav_experiment.py dwb 1")
        return
    
    controller_name = sys.argv[1]
    run_number = int(sys.argv[2])
    
    rclpy.init()
    
    experiment = NavigationExperiment(controller_name, run_number)
    
    try:
        experiment.run_experiment()
    except KeyboardInterrupt:
        experiment.get_logger().info("Experiment interrupted by user")
    finally:
        experiment.stop_bag_recording()
        experiment.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()