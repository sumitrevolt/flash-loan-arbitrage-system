#!/usr/bin/env python3
"""
Automated Retraining Scheduler for MCP System
Manages periodic retraining sessions with intelligent scheduling
"""

import asyncio
import schedule
import time
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass
import pandas as pd
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_retraining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class RetrainingJob:
    """Retraining job configuration"""
    job_id: str
    schedule_type: str  # 'hourly', 'daily', 'weekly', 'monthly'
    schedule_time: str  # Time specification
    models_target: List[str]  # Specific models or 'all'
    min_data_points: int
    performance_threshold: float
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True

class AutomatedRetrainingScheduler:
    """Manages automated retraining of MCP models"""
    
    def __init__(self):
        self.db_path = "retraining_scheduler.db"
        self.continuous_learning_script = "continuous_learning_system.py"
        self.data_collector_script = "real_trading_data_collector.py"
        
        # Default retraining schedules
        self.default_schedules = [
            {
                'job_id': 'hourly_quick_update',
                'schedule_type': 'hourly',
                'schedule_time': '00',  # Every hour at minute 0
                'models_target': ['price_predictor', 'arbitrage_detector'],
                'min_data_points': 50,
                'performance_threshold': 0.02  # 2% improvement required
            },
            {
                'job_id': 'daily_comprehensive_update',
                'schedule_type': 'daily',
                'schedule_time': '02:00',  # 2 AM daily
                'models_target': ['all'],
                'min_data_points': 200,
                'performance_threshold': 0.01  # 1% improvement required
            },
            {
                'job_id': 'weekly_deep_retrain',
                'schedule_type': 'weekly',
                'schedule_time': 'sunday:03:00',  # 3 AM every Sunday
                'models_target': ['all'],
                'min_data_points': 1000,
                'performance_threshold': 0.005  # 0.5% improvement required
            },
            {
                'job_id': 'monthly_full_rebuild',
                'schedule_type': 'monthly',
                'schedule_time': '1:04:00',  # 4 AM on 1st of each month
                'models_target': ['all'],
                'min_data_points': 5000,
                'performance_threshold': 0.001  # Any improvement
            }
        ]
        
        self.running = False
        self.current_jobs = []
    
    async def initialize_database(self):
        """Initialize scheduler database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Retraining jobs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retraining_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    schedule_type TEXT NOT NULL,
                    schedule_time TEXT NOT NULL,
                    models_target TEXT NOT NULL,
                    min_data_points INTEGER NOT NULL,
                    performance_threshold REAL NOT NULL,
                    last_run DATETIME,
                    next_run DATETIME,
                    enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Retraining execution history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retraining_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    execution_start DATETIME NOT NULL,
                    execution_end DATETIME,
                    status TEXT NOT NULL,
                    models_updated INTEGER DEFAULT 0,
                    samples_processed INTEGER DEFAULT 0,
                    average_improvement REAL DEFAULT 0.0,
                    error_message TEXT,
                    log_file TEXT
                )
            ''')
            
            # System health checks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_collector_status TEXT,
                    learning_system_status TEXT,
                    mcp_servers_healthy INTEGER,
                    total_mcp_servers INTEGER,
                    disk_usage_mb REAL,
                    memory_usage_mb REAL
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Retraining scheduler database initialized")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def load_default_schedules(self):
        """Load default retraining schedules"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for schedule_config in self.default_schedules:
                cursor.execute('''
                    INSERT OR REPLACE INTO retraining_jobs 
                    (job_id, schedule_type, schedule_time, models_target, 
                     min_data_points, performance_threshold, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    schedule_config['job_id'],
                    schedule_config['schedule_type'],
                    schedule_config['schedule_time'],
                    json.dumps(schedule_config['models_target']),
                    schedule_config['min_data_points'],
                    schedule_config['performance_threshold'],
                    True
                ))
            
            conn.commit()
            conn.close()
            logger.info("Default retraining schedules loaded")
            
        except Exception as e:
            logger.error(f"Failed to load default schedules: {e}")
    
    async def load_jobs_from_database(self):
        """Load retraining jobs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            df = pd.read_sql_query('''
                SELECT * FROM retraining_jobs WHERE enabled = 1
                ORDER BY job_id
            ''', conn)
            
            conn.close()
            
            jobs = []
            for _, row in df.iterrows():
                job = RetrainingJob(
                    job_id=row['job_id'],
                    schedule_type=row['schedule_type'],
                    schedule_time=row['schedule_time'],
                    models_target=json.loads(row['models_target']),
                    min_data_points=row['min_data_points'],
                    performance_threshold=row['performance_threshold'],
                    last_run=pd.to_datetime(row['last_run']) if row['last_run'] else None,
                    next_run=pd.to_datetime(row['next_run']) if row['next_run'] else None,
                    enabled=bool(row['enabled'])
                )
                jobs.append(job)
            
            self.current_jobs = jobs
            logger.info(f"Loaded {len(jobs)} retraining jobs")
            
        except Exception as e:
            logger.error(f"Failed to load jobs from database: {e}")
    
    def calculate_next_run_time(self, job: RetrainingJob) -> datetime:
        """Calculate next run time for a job"""
        now = datetime.now()
        
        if job.schedule_type == 'hourly':
            minute = int(job.schedule_time)
            next_run = now.replace(minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
        
        elif job.schedule_type == 'daily':
            hour, minute = map(int, job.schedule_time.split(':'))
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif job.schedule_type == 'weekly':
            day, time_str = job.schedule_time.split(':')
            hour, minute = map(int, time_str.split(':'))
            
            days_ahead = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }[day.lower()] - now.weekday()
            
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        elif job.schedule_type == 'monthly':
            day, hour, minute = map(int, job.schedule_time.split(':'))
            
            # Try this month first
            try:
                next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    # Move to next month
                    if now.month == 12:
                        next_run = next_run.replace(year=now.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=now.month + 1)
            except ValueError:
                # Day doesn't exist in current month, move to next month
                if now.month == 12:
                    next_run = datetime(now.year + 1, 1, day, hour, minute)
                else:
                    next_run = datetime(now.year, now.month + 1, day, hour, minute)
        
        else:
            # Default to 1 hour from now
            next_run = now + timedelta(hours=1)
        
        return next_run
    
    async def check_data_availability(self, min_data_points: int) -> bool:
        """Check if enough data is available for retraining"""
        try:
            real_data_db = "real_trading_data.db"
            if not os.path.exists(real_data_db):
                logger.warning("Real trading data database not found")
                return False
            
            conn = sqlite3.connect(real_data_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM market_data 
                WHERE timestamp >= datetime('now', '-24 hours')
            ''')
            
            data_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"Available data points: {data_count}, required: {min_data_points}")
            return data_count >= min_data_points
            
        except Exception as e:
            logger.error(f"Failed to check data availability: {e}")
            return False
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health before retraining"""
        health_status = {
            'data_collector_running': False,
            'mcp_servers_healthy': 0,
            'total_mcp_servers': 31,
            'disk_space_available': True,
            'memory_available': True
        }
        
        try:
            # Check if data collector is running (simplified check)
            if os.path.exists("real_trading_data.db"):
                # Check if database was updated recently
                stat = os.stat("real_trading_data.db")
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                if datetime.now() - last_modified < timedelta(minutes=10):
                    health_status['data_collector_running'] = True
            
            # Check MCP servers health (simplified)
            import aiohttp
            healthy_servers = 0
            
            mcp_ports = list(range(8100, 8121)) + list(range(8200, 8210))
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                for port in mcp_ports:
                    try:
                        async with session.get(f"http://localhost:{port}/health") as response:
                            if response.status == 200:
                                healthy_servers += 1
                    except:
                        continue
            
            health_status['mcp_servers_healthy'] = healthy_servers
            
            # Check disk space (simplified)
            import shutil
            disk_usage = shutil.disk_usage('.')
            free_gb = disk_usage.free / (1024**3)
            health_status['disk_space_available'] = free_gb > 1.0  # At least 1GB free
            
            # Store health check
            await self.store_health_check(health_status)
            
            logger.info(f"System health: {healthy_servers}/{health_status['total_mcp_servers']} servers healthy")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        return health_status
    
    async def store_health_check(self, health_status: Dict):
        """Store health check results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO health_checks 
                (data_collector_status, learning_system_status, mcp_servers_healthy, 
                 total_mcp_servers, disk_usage_mb, memory_usage_mb)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'running' if health_status['data_collector_running'] else 'stopped',
                'unknown',
                health_status['mcp_servers_healthy'],
                health_status['total_mcp_servers'],
                0.0,  # Placeholder
                0.0   # Placeholder
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store health check: {e}")
    
    async def execute_retraining_job(self, job: RetrainingJob) -> Dict[str, Any]:
        """Execute a retraining job"""
        logger.info(f"Executing retraining job: {job.job_id}")
        
        execution_start = datetime.now()
        result = {
            'status': 'failed',
            'models_updated': 0,
            'samples_processed': 0,
            'average_improvement': 0.0,
            'error_message': None
        }
        
        try:
            # Pre-execution checks
            if not await self.check_data_availability(job.min_data_points):
                result['error_message'] = f"Insufficient data points (need {job.min_data_points})"
                return result
            
            health_status = await self.check_system_health()
            if health_status['mcp_servers_healthy'] < 20:  # At least 20 servers should be healthy
                result['error_message'] = f"Too many unhealthy MCP servers ({health_status['mcp_servers_healthy']}/31)"
                return result
            
            # Execute continuous learning
            logger.info("Starting continuous learning execution...")
            
            # Create a temporary script for this specific job
            job_script = f"job_{job.job_id}_{int(time.time())}.py"
            
            # Customize learning parameters based on job
            learning_config = {
                'min_samples_for_training': job.min_data_points,
                'performance_threshold': job.performance_threshold,
                'target_models': job.models_target
            }
            
            # Run the continuous learning system once
            cmd = [sys.executable, self.continuous_learning_script, '--single-run', '--config', json.dumps(learning_config)]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result['status'] = 'success'
                
                # Parse output for metrics (simplified)
                output = stdout.decode()
                if 'models updated' in output.lower():
                    # Extract metrics from output (this would need proper parsing)
                    result['models_updated'] = 1  # Placeholder
                    result['samples_processed'] = job.min_data_points
                    result['average_improvement'] = 5.0  # Placeholder
                
                logger.info(f"Retraining job {job.job_id} completed successfully")
            else:
                result['error_message'] = stderr.decode()
                logger.error(f"Retraining job {job.job_id} failed: {result['error_message']}")
            
            # Clean up temporary files
            if os.path.exists(job_script):
                os.remove(job_script)
            
        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"Retraining job {job.job_id} error: {e}")
        
        finally:
            # Store execution history
            await self.store_execution_history(job.job_id, execution_start, datetime.now(), result)
            
            # Update job last run time
            await self.update_job_last_run(job.job_id, execution_start)
        
        return result
    
    async def store_execution_history(self, job_id: str, start_time: datetime, 
                                    end_time: datetime, result: Dict):
        """Store retraining execution history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO retraining_history 
                (job_id, execution_start, execution_end, status, models_updated,
                 samples_processed, average_improvement, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, start_time, end_time, result['status'],
                result['models_updated'], result['samples_processed'],
                result['average_improvement'], result.get('error_message')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store execution history: {e}")
    
    async def update_job_last_run(self, job_id: str, last_run: datetime):
        """Update job last run time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE retraining_jobs 
                SET last_run = ? 
                WHERE job_id = ?
            ''', (last_run, job_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update job last run: {e}")
    
    async def scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Starting retraining scheduler loop...")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                for job in self.current_jobs:
                    if not job.enabled:
                        continue
                    
                    # Calculate next run if not set
                    if job.next_run is None:
                        job.next_run = self.calculate_next_run_time(job)
                    
                    # Check if it's time to run
                    if current_time >= job.next_run:
                        logger.info(f"Triggering scheduled retraining job: {job.job_id}")
                        
                        # Execute job
                        await self.execute_retraining_job(job)
                        
                        # Calculate next run time
                        job.next_run = self.calculate_next_run_time(job)
                        logger.info(f"Next run for {job.job_id}: {job.next_run}")
                
                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def start_scheduler(self):
        """Start the automated retraining scheduler"""
        logger.info("Starting automated retraining scheduler...")
        
        await self.initialize_database()
        await self.load_default_schedules()
        await self.load_jobs_from_database()
        
        self.running = True
        
        try:
            await self.scheduler_loop()
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.running = False
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Stopping retraining scheduler...")
    
    async def generate_scheduler_report(self) -> Dict:
        """Generate scheduler status report"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get job status
            jobs_df = pd.read_sql_query('''
                SELECT job_id, schedule_type, last_run, next_run, enabled
                FROM retraining_jobs
                ORDER BY job_id
            ''', conn)
            
            # Get recent execution history
            history_df = pd.read_sql_query('''
                SELECT job_id, status, models_updated, average_improvement, execution_start
                FROM retraining_history
                WHERE execution_start >= datetime('now', '-7 days')
                ORDER BY execution_start DESC
            ''', conn)
            
            # Get health checks
            health_df = pd.read_sql_query('''
                SELECT * FROM health_checks
                WHERE timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 1
            ''', conn)
            
            conn.close()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_jobs': len(jobs_df),
                'enabled_jobs': len(jobs_df[jobs_df['enabled'] == 1]) if not jobs_df.empty else 0,
                'recent_executions': len(history_df),
                'successful_executions': len(history_df[history_df['status'] == 'success']) if not history_df.empty else 0,
                'total_models_updated': history_df['models_updated'].sum() if not history_df.empty else 0,
                'average_improvement': history_df['average_improvement'].mean() if not history_df.empty else 0,
                'latest_health_check': health_df.to_dict('records')[0] if not health_df.empty else {},
                'job_schedules': jobs_df.to_dict('records') if not jobs_df.empty else [],
                'recent_executions_detail': history_df.to_dict('records') if not history_df.empty else []
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate scheduler report: {e}")
            return {}
    
    async def add_custom_job(self, job_config: Dict) -> bool:
        """Add a custom retraining job"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO retraining_jobs 
                (job_id, schedule_type, schedule_time, models_target, 
                 min_data_points, performance_threshold, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_config['job_id'],
                job_config['schedule_type'],
                job_config['schedule_time'],
                json.dumps(job_config['models_target']),
                job_config['min_data_points'],
                job_config['performance_threshold'],
                job_config.get('enabled', True)
            ))
            
            conn.commit()
            conn.close()
            
            # Reload jobs
            await self.load_jobs_from_database()
            
            logger.info(f"Added custom retraining job: {job_config['job_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom job: {e}")
            return False

async def main():
    """Main function"""
    scheduler = AutomatedRetrainingScheduler()
    
    try:
        await scheduler.start_scheduler()
    except KeyboardInterrupt:
        logger.info("Automated retraining scheduler stopped")
    finally:
        scheduler.stop_scheduler()

if __name__ == "__main__":
    asyncio.run(main())
