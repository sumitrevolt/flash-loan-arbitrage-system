# -*- coding: utf-8 -*-
"""
Log Aggregator for MCP Coordination System

This module provides centralized log collection, aggregation, and analysis
for all MCP servers and coordination components.
"""

from collections import deque, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import asyncio
import gzip
import json
import logging
import logging.handlers
import re
import threading

from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogSource(Enum):
    """Log source types"""
    MCP_SERVER = "mcp_server"
    HEALTH_MONITOR = "health_monitor"
    DEPLOYMENT_MANAGER = "deployment_manager"
    DASHBOARD = "dashboard"
    CONFIG_MANAGER = "config_manager"
    LANGCHAIN = "langchain"
    AUTOGEN = "autogen"
    SYSTEM = "system"


@dataclass
class LogEntry:
    """Individual log entry"""
    timestamp: datetime
    level: LogLevel
    source: LogSource
    component: str
    message: str
    server_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "source": self.source.value,
            "component": self.component,
            "message": self.message,
            "server_id": self.server_id,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "stack_trace": self.stack_trace



@dataclass
class LogPattern:
    """Log pattern for analysis"""
    name: str
    pattern: str
    severity: LogLevel
    description: str
    action_required: bool = False
    auto_resolve: bool = False


@dataclass
class LogAlert:
    """Log-based alert"""
    pattern_name: str
    count: int
    time_window: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_components: Set[str]
    sample_entries: List[LogEntry]


class LogAggregator:
    """
    Centralized log aggregation and analysis system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_config = config.get("logging", {})
        
        # Log storage
        self.log_buffer: deque[LogEntry] = deque(maxlen=10000)  # In-memory buffer
        self.log_index: Dict[str, List[LogEntry]] = defaultdict(list)  # Indexed by component
        
        # File logging
        self.log_dir = Path(self.log_config.get("log_dir", "logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_log_size = self.log_config.get("max_log_size", 100 * 1024 * 1024)  # 100MB
        self.backup_count = self.log_config.get("backup_count", 10)
        self.compress_logs = self.log_config.get("compress_logs", True)
        
        # Log analysis
        self.log_patterns = self._initialize_log_patterns()
        self.pattern_matches: Dict[str, List[datetime]] = defaultdict(list)
        self.active_alerts: Dict[str, LogAlert] = {}
        
        # Real-time streaming
        self.log_subscribers: List[asyncio.Queue] = []
        self.websocket_connections: List[Any] = []  # WebSocket connections for real-time logs
        
        # Background tasks
        self.log_processor_task: Optional[asyncio.Task] = None
        self.log_analyzer_task: Optional[asyncio.Task] = None
        self.log_cleanup_task: Optional[asyncio.Task] = None
        self.file_writer_task: Optional[asyncio.Task] = None
        
        # Threading for file I/O
        self.file_write_queue: asyncio.Queue = asyncio.Queue()
        self.file_writer_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            "total_logs": 0,
            "logs_by_level": {level.value: 0 for level in LogLevel},
            "logs_by_source": {source.value: 0 for source in LogSource},
            "patterns_matched": 0,
            "alerts_generated": 0,
            "files_written": 0,
            "bytes_written": 0

        
        # Setup file loggers
        self._setup_file_loggers()
        
        logger.info("[INIT] Log Aggregator initialized")
    
    def _initialize_log_patterns(self) -> List[LogPattern]:
        """Initialize log patterns for analysis"""
        return [
            LogPattern(
                name="server_startup_failed",
                pattern=r"Failed to (start|deploy|initialize) server",
                severity=LogLevel.ERROR,
                description="Server startup failure detected",
                action_required=True
            ),
            LogPattern(
                name="health_check_failed",
                pattern=r"Health check failed|Server (unhealthy|down|unreachable)",
                severity=LogLevel.WARNING,
                description="Health check failure detected",
                action_required=True
            ),
            LogPattern(
                name="circuit_breaker_open",
                pattern=r"Circuit breaker (opened|open)",
                severity=LogLevel.CRITICAL,
                description="Circuit breaker opened",
                action_required=True
            ),
            LogPattern(
                name="high_error_rate",
                pattern=r"Error rate|Failed request|Exception|Traceback",
                severity=LogLevel.ERROR,
                description="High error rate detected",
                action_required=False
            ),
            LogPattern(
                name="memory_warning",
                pattern=r"Memory (usage|warning|limit)|Out of memory|OOM",
                severity=LogLevel.WARNING,
                description="Memory usage warning",
                action_required=True
            ),
            LogPattern(
                name="connection_timeout",
                pattern=r"Connection (timeout|failed|refused)|Timeout error",
                severity=LogLevel.WARNING,
                description="Connection timeout detected",
                action_required=False
            ),
            LogPattern(
                name="authentication_failure",
                pattern=r"Authentication (failed|denied)|Unauthorized|Access denied",
                severity=LogLevel.WARNING,
                description="Authentication failure detected",
                action_required=True
            ),
            LogPattern(
                name="disk_space_warning",
                pattern=r"Disk (space|full)|No space left|Storage warning",
                severity=LogLevel.WARNING,
                description="Disk space warning",
                action_required=True
            ),
            LogPattern(
                name="configuration_error",
                pattern=r"Configuration (error|invalid|missing)|Config validation failed",
                severity=LogLevel.ERROR,
                description="Configuration error detected",
                action_required=True
            ),
            LogPattern(
                name="deployment_success",
                pattern=r"(Deployment|Server|Service) (completed|started|ready|operational)",
                severity=LogLevel.INFO,
                description="Successful deployment detected",
                action_required=False,
                auto_resolve=True


    
    def _setup_file_loggers(self):
        """Setup file logging handlers"""
        try:
            # Main aggregated log file
            main_log_file = self.log_dir / "mcp_aggregated.log"
            main_handler = logging.handlers.RotatingFileHandler(
                main_log_file,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count

            main_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

            
            # Component-specific log files
            self.component_handlers = {}
            for source in LogSource:
                log_file = self.log_dir / f"{source.value}.log"
                handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=self.max_log_size // 5,  # Smaller files for components
                    backupCount=5

                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'

                self.component_handlers[source] = handler
            
            # Error-only log file
            error_log_file = self.log_dir / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=self.max_log_size // 2,
                backupCount=self.backup_count

            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'

            
            logger.info("[SETUP] File logging handlers configured")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to setup file loggers: {e}")
    
    async def initialize(self):
        """Initialize the log aggregator"""
        try:
            # Start background tasks
            self.log_processor_task = asyncio.create_task(self._log_processor_loop())
            self.log_analyzer_task = asyncio.create_task(self._log_analyzer_loop())
            self.log_cleanup_task = asyncio.create_task(self._log_cleanup_loop())
            self.file_writer_task = asyncio.create_task(self._file_writer_loop())
            
            # Start file writer thread
            self.file_writer_thread = threading.Thread(target=self._file_writer_thread_func)
            self.file_writer_thread.daemon = True
            self.file_writer_thread.start()
            
            logger.info("[OK] Log Aggregator initialized")
            
        except Exception as e:
            logger.error(f"[ERROR] Log Aggregator initialization failed: {e}")
            raise
    
    async def add_log_entry(self, entry: LogEntry):
        """Add a log entry to the aggregator"""
        try:
            # Add to buffer
            self.log_buffer.append(entry)
            
            # Index by component
            self.log_index[entry.component].append(entry)
            
            # Update statistics
            self.stats["total_logs"] += 1
            self.stats["logs_by_level"][entry.level.value] += 1
            self.stats["logs_by_source"][entry.source.value] += 1
            
            # Queue for file writing
            await self.file_write_queue.put(entry)
            
            # Stream to subscribers
            await self._stream_to_subscribers(entry)
            
            # Trigger analysis if it's an error or warning
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.WARNING]:
                await self._analyze_log_entry(entry)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to add log entry: {e}")
    
    async def log(self, level: LogLevel, source: LogSource, component: str, message: str, 
                  server_id: Optional[str] = None, request_id: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None, stack_trace: Optional[str] = None):
        """Convenience method to log a message"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            source=source,
            component=component,
            message=message,
            server_id=server_id,
            request_id=request_id,
            metadata=metadata or {},
            stack_trace=stack_trace

        
        await self.add_log_entry(entry)
    
    async def _stream_to_subscribers(self, entry: LogEntry):
        """Stream log entry to real-time subscribers"""
        try:
            # Stream to queue subscribers
            disconnected_queues = []
            for queue in self.log_subscribers:
                try:
                    queue.put_nowait(entry)
                except asyncio.QueueFull:
                    # Remove full queues
                    disconnected_queues.append(queue)
                except Exception:
                    disconnected_queues.append(queue)
            
            # Remove disconnected queues
            for queue in disconnected_queues:
                self.log_subscribers.remove(queue)
            
            # Stream to WebSocket connections
            disconnected_ws = []
            for ws in self.websocket_connections:
                try:
                    await ws.send_json(entry.to_dict())
                except Exception:
                    disconnected_ws.append(ws)
            
            # Remove disconnected WebSocket connections
            for ws in disconnected_ws:
                self.websocket_connections.remove(ws)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to stream log entry: {e}")
    
    async def _analyze_log_entry(self, entry: LogEntry):
        """Analyze log entry for patterns"""
        try:
            for pattern in self.log_patterns:
                if re.search(pattern.pattern, entry.message, re.IGNORECASE):
                    # Pattern matched
                    self.pattern_matches[pattern.name].append(entry.timestamp)
                    self.stats["patterns_matched"] += 1
                    
                    # Check if we should generate an alert
                    await self._check_pattern_alert(pattern, entry)
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to analyze log entry: {e}")
    
    async def _check_pattern_alert(self, pattern: LogPattern, entry: LogEntry):
        """Check if a pattern should trigger an alert"""
        try:
            # Get recent matches for this pattern
            cutoff_time = datetime.now() - timedelta(minutes=15)  # 15-minute window
            recent_matches = [
                ts for ts in self.pattern_matches[pattern.name] 
                if ts > cutoff_time

            
            # Determine alert threshold based on pattern severity
            threshold = {
                LogLevel.CRITICAL: 1,
                LogLevel.ERROR: 3,
                LogLevel.WARNING: 5,
                LogLevel.INFO: 10
            }.get(pattern.severity, 5)
            
            if len(recent_matches) >= threshold:
                # Generate or update alert
                alert_key = f"{pattern.name}_{entry.component}"
                
                if alert_key in self.active_alerts:
                    # Update existing alert
                    alert = self.active_alerts[alert_key]
                    alert.count = len(recent_matches)
                    alert.last_occurrence = entry.timestamp
                    alert.affected_components.add(entry.component)
                    if len(alert.sample_entries) < 5:
                        alert.sample_entries.append(entry)
                else:
                    # Create new alert
                    alert = LogAlert(
                        pattern_name=pattern.name,
                        count=len(recent_matches),
                        time_window=15,
                        first_occurrence=recent_matches[0],
                        last_occurrence=entry.timestamp,
                        affected_components={entry.component},
                        sample_entries=[entry]

                    self.active_alerts[alert_key] = alert
                    self.stats["alerts_generated"] += 1
                    
                    logger.warning(f"[ALERT] Log pattern alert generated: {pattern.name} - {pattern.description}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to check pattern alert: {e}")
    
    async def _log_processor_loop(self):
        """Background task for log processing"""
        while True:
            try:
                await asyncio.sleep(1)
                
                # Process log buffer if needed
                # This is where we could add additional processing like:
                # - Log enrichment
                # - Custom filtering
                # - External system integration
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Log processor loop failed: {e}")
    
    async def _log_analyzer_loop(self):
        """Background task for log analysis"""
        while True:
            try:
                await asyncio.sleep(60)  # Analyze every minute
                
                # Cleanup old pattern matches
                cutoff_time = datetime.now() - timedelta(hours=1)
                for pattern_name in self.pattern_matches:
                    self.pattern_matches[pattern_name] = [
                        ts for ts in self.pattern_matches[pattern_name]
                        if ts > cutoff_time

                
                # Auto-resolve alerts
                resolved_alerts = []
                for alert_key, alert in self.active_alerts.items():
                    if (datetime.now() - alert.last_occurrence).total_seconds() > 900:  # 15 minutes
                        resolved_alerts.append(alert_key)
                
                for alert_key in resolved_alerts:
                    del self.active_alerts[alert_key]
                    logger.info(f"[ALERT] Auto-resolved log alert: {alert_key}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Log analyzer loop failed: {e}")
    
    async def _log_cleanup_loop(self):
        """Background task for log cleanup"""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                
                # Cleanup old log entries from index
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                for component in self.log_index:
                    original_count = len(self.log_index[component])
                    self.log_index[component] = [
                        entry for entry in self.log_index[component]
                        if entry.timestamp > cutoff_time

                    cleaned_count = original_count - len(self.log_index[component])
                    
                    if cleaned_count > 0:
                        logger.debug(f"[CLEANUP] Cleaned {cleaned_count} old log entries for {component}")
                
                # Compress old log files
                if self.compress_logs:
                    await self._compress_old_logs()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] Log cleanup loop failed: {e}")
    
    async def _file_writer_loop(self):
        """Background task for writing logs to files"""
        while True:
            try:
                # Get log entry from queue
                entry = await self.file_write_queue.get()
                
                # Write to appropriate files
                await self._write_to_files(entry)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ERROR] File writer loop failed: {e}")
    
    def _file_writer_thread_func(self):
        """Thread function for file writing"""
        # This would handle the actual file I/O in a separate thread
        # to avoid blocking the async event loop
        pass
    
    async def _write_to_files(self, entry: LogEntry):
        """Write log entry to appropriate files"""
        try:
            # Format log entry
            log_line = f"{entry.timestamp.isoformat()} - {entry.level.value} - {entry.component} - {entry.message}"
            if entry.metadata:
                log_line += f" - Metadata: {json.dumps(entry.metadata)}"
            if entry.stack_trace:
                log_line += f"\nStack trace: {entry.stack_trace}"
            log_line += "\n"
            
            # Write to main log file
            main_log_file = self.log_dir / "mcp_aggregated.log"
            with open(main_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
            # Write to component-specific log file
            component_log_file = self.log_dir / f"{entry.source.value}.log"
            with open(component_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
            # Write to error log if it's an error
            if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_log_file = self.log_dir / "errors.log"
                with open(error_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line)
            
            # Update statistics
            self.stats["files_written"] += 1
            self.stats["bytes_written"] += len(log_line.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to write log to file: {e}")
    
    async def _compress_old_logs(self):
        """Compress old log files"""
        try:
            for log_file in self.log_dir.glob("*.log.*"):
                if not log_file.name.endswith('.gz'):
                    # Compress the file
                    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    # Remove original file
                    log_file.unlink()
                    logger.debug(f"[COMPRESSION] Compressed log file: {log_file}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to compress old logs: {e}")
    
    async def subscribe_to_logs(self) -> asyncio.Queue:
        """Subscribe to real-time log stream"""
        queue = asyncio.Queue(maxsize=1000)
        self.log_subscribers.append(queue)
        return queue
    
    async def add_websocket_connection(self, websocket):
        """Add WebSocket connection for real-time log streaming"""
        self.websocket_connections.append(websocket)
    
    async def remove_websocket_connection(self, websocket):
        """Remove WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
    
    async def search_logs(self, query: str, start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None, level: Optional[LogLevel] = None,
                         source: Optional[LogSource] = None, component: Optional[str] = None,
                         limit: int = 100) -> List[LogEntry]:
        """Search logs with filters"""
        try:
            results = []
            search_regex = re.compile(query, re.IGNORECASE) if query else None
            
            # Search through log buffer
            for entry in reversed(self.log_buffer):
                # Apply filters
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                if level and entry.level != level:
                    continue
                if source and entry.source != source:
                    continue
                if component and entry.component != component:
                    continue
                
                # Apply text search
                if search_regex:
                    if not (search_regex.search(entry.message) or 
                           search_regex.search(entry.component) or
                           (entry.metadata and search_regex.search(json.dumps(entry.metadata)))):
                        continue
                
                results.append(entry)
                
                if len(results) >= limit:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to search logs: {e}")
            return []
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """Get comprehensive log statistics"""
        try:
            # Calculate recent activity
            recent_time = datetime.now() - timedelta(minutes=15)
            recent_logs = [entry for entry in self.log_buffer if entry.timestamp > recent_time]
            
            recent_stats = {
                "total": len(recent_logs),
                "by_level": {level.value: 0 for level in LogLevel},
                "by_source": {source.value: 0 for source in LogSource}

            
            for entry in recent_logs:
                recent_stats["by_level"][entry.level.value] += 1
                recent_stats["by_source"][entry.source.value] += 1
            
            return {
                "log_aggregator_status": "operational",
                "buffer_size": len(self.log_buffer),
                "total_statistics": self.stats,
                "recent_activity": recent_stats,
                "active_patterns": len(self.pattern_matches),
                "active_alerts": len(self.active_alerts),
                "log_files": {
                    "directory": str(self.log_dir),
                    "files": [f.name for f in self.log_dir.glob("*.log")]
                },
                "subscribers": {
                    "queue_subscribers": len(self.log_subscribers),
                    "websocket_connections": len(self.websocket_connections)
                },
                "background_tasks": {
                    "processor": self.log_processor_task is not None and not self.log_processor_task.done(),
                    "analyzer": self.log_analyzer_task is not None and not self.log_analyzer_task.done(),
                    "cleanup": self.log_cleanup_task is not None and not self.log_cleanup_task.done(),
                    "file_writer": self.file_writer_task is not None and not self.file_writer_task.done()


            
        except Exception as e:
            logger.error(f"[ERROR] Failed to get log statistics: {e}")
            return {"error": str(e)}
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active log-based alerts"""
        return [
            {
                "alert_key": alert_key,
                "pattern_name": alert.pattern_name,
                "count": alert.count,
                "time_window": alert.time_window,
                "first_occurrence": alert.first_occurrence.isoformat(),
                "last_occurrence": alert.last_occurrence.isoformat(),
                "affected_components": list(alert.affected_components),
                "sample_messages": [entry.message for entry in alert.sample_entries[:3]]

            for alert_key, alert in self.active_alerts.items()

    
    async def export_logs(self, format: str = "json", start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> str:
        """Export logs in specified format"""
        try:
            # Filter logs by time range
            logs_to_export = []
            for entry in self.log_buffer:
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                logs_to_export.append(entry)
            
            if format.lower() == "json":
                return json.dumps([entry.to_dict() for entry in logs_to_export], indent=2)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(["timestamp", "level", "source", "component", "message", "server_id", "request_id"])
                
                # Write data
                for entry in logs_to_export:
                    writer.writerow([
                        entry.timestamp.isoformat(),
                        entry.level.value,
                        entry.source.value,
                        entry.component,
                        entry.message,
                        entry.server_id or "",
                        entry.request_id or ""

                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to export logs: {e}")
            return ""
    
    async def shutdown(self):
        """Shutdown the log aggregator"""
        logger.info("[SHUTDOWN] Shutting down Log Aggregator...")
        
        # Cancel background tasks
        tasks = [
            self.log_processor_task,
            self.log_analyzer_task,
            self.log_cleanup_task,
            self.file_writer_task

        
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close WebSocket connections
        for ws in self.websocket_connections:
            try:
                await ws.close()
            except:
                pass
        
        # Write remaining log entries
        while not self.file_write_queue.empty():
            try:
                entry = self.file_write_queue.get_nowait()
                await self._write_to_files(entry)
            except:
                break
        
        logger.info("[SHUTDOWN] Log Aggregator shutdown complete")