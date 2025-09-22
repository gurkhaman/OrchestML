#!/usr/bin/env python3

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json
import logging

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("psycopg2 not installed. Run: uv add psycopg2-binary")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str | None = None):
        if connection_string is None:
            connection_string = "postgresql://postgres:password@localhost:32768/monitoring"
        
        self.connection_string = connection_string
        self.connection: Any = None
        
    def connect(self):
        """Establish connection to TimescaleDB"""
        try:
            import psycopg2
            self.connection = psycopg2.connect(self.connection_string)
            self.connection.autocommit = True
            logger.info("Successfully connected to TimescaleDB")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: tuple | None = None) -> List[Dict]:
        """Execute a query and return results"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            import psycopg2.extras
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def insert_navigation_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Insert navigation metrics into database"""
        query = """
        INSERT INTO navigation_metrics (
            timestamp, controller_type, run_id, navigation_time, 
            collision_count, recovery_count, total_recoveries,
            goal1_time, goal2_time, min_distance, avg_distance
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        params = (
            metrics.get('timestamp', datetime.now(timezone.utc)),
            metrics.get('controller_type'),
            metrics.get('run_id'),
            metrics.get('navigation_time'),
            metrics.get('collision_count'),
            metrics.get('recovery_count'),
            metrics.get('total_recoveries'),
            metrics.get('goal1_time'),
            metrics.get('goal2_time'),
            metrics.get('min_distance'),
            metrics.get('avg_distance')
        )
        
        try:
            if not self.connection:
                if not self.connect():
                    return False
                    
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                logger.info(f"Inserted metrics for {metrics.get('run_id')}")
                return True
        except Exception as e:
            logger.error(f"Failed to insert metrics: {e}")
            return False
    
    def get_baseline_metrics(self, controller_type: str) -> Optional[Dict[str, float]]:
        """Get baseline metrics for a controller type"""
        query = """
        SELECT 
            AVG(navigation_time) as avg_navigation_time,
            STDDEV(navigation_time) as std_navigation_time,
            AVG(collision_count) as avg_collision_count,
            STDDEV(collision_count) as std_collision_count,
            AVG(recovery_count) as avg_recovery_count,
            STDDEV(recovery_count) as std_recovery_count,
            COUNT(*) as sample_size
        FROM navigation_metrics 
        WHERE controller_type = %s
        """
        
        results = self.execute_query(query, (controller_type,))
        if results and results[0]['avg_navigation_time']:
            return results[0]
        return None
    
    def calculate_and_store_baseline(self, controller_type: str) -> bool:
        """Calculate baseline from existing data and store it"""
        baseline = self.get_baseline_metrics(controller_type)
        if not baseline:
            logger.warning(f"No data available for {controller_type} baseline calculation")
            return False
        
        # Calculate thresholds (using your rationale: 1.5x baseline + 1 std dev)
        nav_time_threshold = baseline['avg_navigation_time'] + 1.5 * (baseline['std_navigation_time'] or 0)
        collision_threshold = baseline['avg_collision_count'] + (baseline['std_collision_count'] or 0)
        recovery_threshold = baseline['avg_recovery_count'] + 1.5 * (baseline['std_recovery_count'] or 0)
        
        # Store in performance_baselines table
        query = """
        INSERT INTO performance_baselines (
            controller_type, avg_navigation_time, avg_collision_count, avg_recovery_count,
            nav_time_threshold, collision_threshold, recovery_threshold
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (controller_type) DO UPDATE SET
            avg_navigation_time = EXCLUDED.avg_navigation_time,
            avg_collision_count = EXCLUDED.avg_collision_count,
            avg_recovery_count = EXCLUDED.avg_recovery_count,
            nav_time_threshold = EXCLUDED.nav_time_threshold,
            collision_threshold = EXCLUDED.collision_threshold,
            recovery_threshold = EXCLUDED.recovery_threshold,
            created_at = NOW()
        """
        
        params = (
            controller_type,
            baseline['avg_navigation_time'],
            baseline['avg_collision_count'],
            baseline['avg_recovery_count'],
            nav_time_threshold,
            collision_threshold,
            recovery_threshold
        )
        
        try:
            if not self.connection:
                if not self.connect():
                    return False
                    
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                logger.info(f"Stored baseline for {controller_type}: "
                          f"nav_time={baseline['avg_navigation_time']:.1f}s (threshold: {nav_time_threshold:.1f}s)")
                return True
        except Exception as e:
            logger.error(f"Failed to store baseline: {e}")
            return False
    
    def check_performance_degradation(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current metrics indicate performance degradation"""
        controller_type = metrics.get('controller_type')
        
        # Get stored thresholds
        query = """
        SELECT nav_time_threshold, collision_threshold, recovery_threshold,
               avg_navigation_time, avg_collision_count, avg_recovery_count
        FROM performance_baselines 
        WHERE controller_type = %s
        """
        
        baseline_results = self.execute_query(query, (controller_type,))
        if not baseline_results:
            return {'degraded': False, 'reason': 'No baseline available'}
        
        baseline = baseline_results[0]
        
        # Check degradation conditions
        degradation_flags = {
            'navigation_time_degraded': metrics.get('navigation_time', 0) > baseline['nav_time_threshold'],
            'collision_spike': metrics.get('collision_count', 0) > baseline['collision_threshold'],
            'recovery_spike': metrics.get('recovery_count', 0) > baseline['recovery_threshold']
        }
        
        is_degraded = any(degradation_flags.values())
        
        result = {
            'degraded': is_degraded,
            'flags': degradation_flags,
            'current_metrics': {
                'navigation_time': metrics.get('navigation_time'),
                'collision_count': metrics.get('collision_count'),
                'recovery_count': metrics.get('recovery_count')
            },
            'baseline_thresholds': {
                'nav_time_threshold': baseline['nav_time_threshold'],
                'collision_threshold': baseline['collision_threshold'],
                'recovery_threshold': baseline['recovery_threshold']
            },
            'baseline_averages': {
                'avg_navigation_time': baseline['avg_navigation_time'],
                'avg_collision_count': baseline['avg_collision_count'],
                'avg_recovery_count': baseline['avg_recovery_count']
            }
        }
        
        if is_degraded:
            degraded_metrics = [k for k, v in degradation_flags.items() if v]
            result['reason'] = f"Performance degraded in: {', '.join(degraded_metrics)}"
            logger.warning(f"Performance degradation detected for {controller_type}: {result['reason']}")
        
        return result
    
    def log_trigger_event(self, trigger_data: Dict[str, Any]) -> bool:
        """Log a trigger event to the database"""
        query = """
        INSERT INTO trigger_events (
            trigger_type, current_controller, triggered_by, 
            current_metrics, action_taken, status
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (
            trigger_data.get('trigger_type'),
            trigger_data.get('current_controller'),
            trigger_data.get('triggered_by'),
            json.dumps(trigger_data.get('current_metrics', {})),
            trigger_data.get('action_taken'),
            trigger_data.get('status', 'pending')
        )
        
        try:
            if not self.connection:
                if not self.connect():
                    return False
                    
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                logger.info(f"Logged trigger event: {trigger_data.get('trigger_type')}")
                return True
        except Exception as e:
            logger.error(f"Failed to log trigger event: {e}")
            return False
    
    def get_recent_metrics(self, controller_type: str | None = None, limit: int = 10) -> List[Dict]:
        """Get recent navigation metrics"""
        if controller_type:
            query = """
            SELECT * FROM navigation_metrics 
            WHERE controller_type = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            params = (controller_type, limit)
        else:
            query = """
            SELECT * FROM navigation_metrics 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            params = (limit,)
        
        return self.execute_query(query, params)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        query = """
        SELECT 
            controller_type,
            COUNT(*) as total_runs,
            AVG(navigation_time) as avg_nav_time,
            MIN(navigation_time) as min_nav_time,
            MAX(navigation_time) as max_nav_time,
            AVG(collision_count) as avg_collisions,
            AVG(recovery_count) as avg_recoveries
        FROM navigation_metrics 
        GROUP BY controller_type
        ORDER BY controller_type
        """
        
        results = self.execute_query(query)
        
        # Also get trigger events
        trigger_query = "SELECT * FROM trigger_events ORDER BY timestamp DESC"
        triggers = self.execute_query(trigger_query)
        
        return {
            'performance_by_controller': results,
            'trigger_events': triggers
        }

if __name__ == "__main__":
    # Test the database connection
    db = DatabaseManager()
    if db.connect():
        print("✓ Database connection successful")
        
        # Test basic query
        results = db.execute_query("SELECT NOW() as current_time")
        if results:
            print(f"✓ Query test successful: {results[0]['current_time']}")
        
        db.disconnect()
    else:
        print("✗ Database connection failed")