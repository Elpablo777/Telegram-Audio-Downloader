"""
📊 Performance Monitoring and Benchmarks for Telegram Audio Downloader

Enterprise-level performance monitoring with comprehensive metrics collection,
automated benchmarks, and performance regression detection.
"""

import time
import asyncio
import psutil
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class PerformanceMetric:
    """Data class for storing performance metrics."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class BenchmarkResult:
    """Data class for storing benchmark results."""
    test_name: str
    duration_ms: float
    memory_peak_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """
    Enterprise-level performance monitoring system.
    
    Features:
    - Real-time metrics collection
    - Memory usage tracking
    - CPU utilization monitoring
    - I/O performance measurement
    - Automated benchmarking
    - Performance regression detection
    """
    
    def __init__(self):
        self.metrics: list[PerformanceMetric] = []
        self.benchmarks: list[BenchmarkResult] = []
        self.start_time = time.time()
        self.process = psutil.Process()
        
    def record_metric(self, name: str, value: float, unit: str, context: Dict[str, Any] = None):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {},
        )
        self.metrics.append(metric)
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process_memory = self.process.memory_info()
            process_cpu = self.process.cpu_percent()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_mb': memory.available / (1024 * 1024),
                    'disk_usage_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                },
                'process': {
                    'memory_rss_mb': process_memory.rss / (1024 * 1024),
                    'memory_vms_mb': process_memory.vms / (1024 * 1024),
                    'cpu_percent': process_cpu,
                    'threads': self.process.num_threads(),
                },
                'python': {
                    'version': sys.version_info[:3],
                    'platform': sys.platform,
                },
            }
        except Exception as e:
            return {'error': str(e)}
            
    async def benchmark_async_operation(
        self, 
        operation_name: str, 
        operation_func, 
        *args, 
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark an async operation with comprehensive metrics."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024 * 1024)
        start_cpu = self.process.cpu_percent()
        
        try:
            # Execute the operation
            if asyncio.iscoroutinefunction(operation_func):
                result = await operation_func(*args, **kwargs)
            else:
                result = operation_func(*args, **kwargs)
                
            # Calculate metrics
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self.process.memory_info().rss / (1024 * 1024)
            memory_peak = max(start_memory, end_memory)
            cpu_usage = self.process.cpu_percent()
            
            benchmark = BenchmarkResult(
                test_name=operation_name,
                duration_ms=duration_ms,
                memory_peak_mb=memory_peak,
                cpu_usage_percent=cpu_usage,
                success=True,
                metadata={'result_type': type(result).__name__ if result else 'None'},
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self.process.memory_info().rss / (1024 * 1024)
            
            benchmark = BenchmarkResult(
                test_name=operation_name,
                duration_ms=duration_ms,
                memory_peak_mb=max(start_memory, end_memory),
                cpu_usage_percent=self.process.cpu_percent(),
                success=False,
                error_message=str(e),
            )
            
        self.benchmarks.append(benchmark)
        return benchmark
        
    def benchmark_sync_operation(
        self, 
        operation_name: str, 
        operation_func, 
        *args, 
        **kwargs
    ) -> BenchmarkResult:
        """Benchmark a synchronous operation."""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / (1024 * 1024)
        
        try:
            result = operation_func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self.process.memory_info().rss / (1024 * 1024)
            memory_peak = max(start_memory, end_memory)
            
            benchmark = BenchmarkResult(
                test_name=operation_name,
                duration_ms=duration_ms,
                memory_peak_mb=memory_peak,
                cpu_usage_percent=self.process.cpu_percent(),
                success=True,
                metadata={'result_type': type(result).__name__ if result else 'None'},
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self.process.memory_info().rss / (1024 * 1024)
            
            benchmark = BenchmarkResult(
                test_name=operation_name,
                duration_ms=duration_ms,
                memory_peak_mb=max(start_memory, end_memory),
                cpu_usage_percent=self.process.cpu_percent(),
                success=False,
                error_message=str(e),
            )
            
        self.benchmarks.append(benchmark)
        return benchmark
        
    def export_metrics_json(self, filepath: Path = None) -> str:
        """Export all collected metrics to JSON."""
        if filepath is None:
            filepath = Path(f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
        export_data = {
            'session_info': {
                'start_time': self.start_time,
                'export_time': time.time(),
                'duration_seconds': time.time() - self.start_time,
                'system_info': self.get_system_metrics(),
            },
            'metrics': [asdict(metric) for metric in self.metrics],
            'benchmarks': [asdict(benchmark) for benchmark in self.benchmarks],
            'summary': self.get_performance_summary(),
        }
        
        # Convert datetime objects to ISO strings for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
        json_data = json.dumps(export_data, indent=2, default=json_serializer)
        
        if filepath:
            filepath.write_text(json_data)
            
        return json_data
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.benchmarks:
            return {'status': 'No benchmarks recorded'}
            
        successful_benchmarks = [b for b in self.benchmarks if b.success]
        failed_benchmarks = [b for b in self.benchmarks if not b.success]
        
        if successful_benchmarks:
            durations = [b.duration_ms for b in successful_benchmarks]
            memory_peaks = [b.memory_peak_mb for b in successful_benchmarks]
            
            summary = {
                'total_benchmarks': len(self.benchmarks),
                'successful': len(successful_benchmarks),
                'failed': len(failed_benchmarks),
                'success_rate': len(successful_benchmarks) / len(self.benchmarks) * 100,
                'performance': {
                    'avg_duration_ms': sum(durations) / len(durations),
                    'min_duration_ms': min(durations),
                    'max_duration_ms': max(durations),
                    'avg_memory_mb': sum(memory_peaks) / len(memory_peaks),
                    'peak_memory_mb': max(memory_peaks),
                },
            }
        else:
            summary = {
                'total_benchmarks': len(self.benchmarks),
                'successful': 0,
                'failed': len(failed_benchmarks),
                'success_rate': 0.0,
                'error_summary': [b.error_message for b in failed_benchmarks],
            }
            
        return summary


class AutomatedBenchmarks:
    """Automated benchmark suite for common operations."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        
    async def run_file_io_benchmarks(self) -> list[BenchmarkResult]:
        """Run file I/O performance benchmarks."""
        results = []
        
        # Test file writing performance
        async def write_test_file():
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                test_data = "x" * 1024 * 100  # 100KB of data
                f.write(test_data)
                f.flush()
                return f.name
                
        result = await self.monitor.benchmark_async_operation(
            "file_write_100kb", write_test_file
        )
        results.append(result)
        
        # Test file reading performance
        def read_test_file():
            with tempfile.NamedTemporaryFile(mode='w+', delete=True) as f:
                test_data = "x" * 1024 * 100  # 100KB of data
                f.write(test_data)
                f.seek(0)
                content = f.read()
                return len(content)
                
        result = self.monitor.benchmark_sync_operation(
            "file_read_100kb", read_test_file
        )
        results.append(result)
        
        return results
        
    async def run_async_benchmarks(self) -> list[BenchmarkResult]:
        """Run async operation benchmarks."""
        results = []
        
        # Test async sleep performance (minimal overhead test)
        async def async_sleep_test():
            await asyncio.sleep(0.001)  # 1ms sleep
            return "completed"
            
        result = await self.monitor.benchmark_async_operation(
            "async_sleep_1ms", async_sleep_test
        )
        results.append(result)
        
        # Test async task creation
        async def async_task_creation():
            tasks = []
            for i in range(10):
                task = asyncio.create_task(asyncio.sleep(0.001))
                tasks.append(task)
            await asyncio.gather(*tasks)
            return len(tasks)
            
        result = await self.monitor.benchmark_async_operation(
            "async_task_creation_10", async_task_creation
        )
        results.append(result)
        
        return results
        
    async def run_memory_benchmarks(self) -> list[BenchmarkResult]:
        """Run memory usage benchmarks."""
        results = []
        
        # Test memory allocation
        def memory_allocation_test():
            # Allocate 10MB of data
            data = [0] * (1024 * 1024 * 10 // 8)  # Approximately 10MB of integers
            return len(data)
            
        result = self.monitor.benchmark_sync_operation(
            "memory_allocation_10mb", memory_allocation_test
        )
        results.append(result)
        
        # Test string operations
        def string_operations_test():
            base_string = "test_string_" * 1000
            operations = []
            for i in range(100):
                operations.append(base_string.upper())
                operations.append(base_string.lower())
                operations.append(base_string.replace("_", "-"))
            return len(operations)
            
        result = self.monitor.benchmark_sync_operation(
            "string_operations_300", string_operations_test
        )
        results.append(result)
        
        return results
        
    async def run_full_benchmark_suite(self) -> Dict[str, list[BenchmarkResult]]:
        """Run the complete benchmark suite."""
        print("🚀 Starting Full Performance Benchmark Suite...")
        
        suite_results = {
            'file_io': await self.run_file_io_benchmarks(),
            'async_operations': await self.run_async_benchmarks(),
            'memory_operations': await self.run_memory_benchmarks(),
        }
        
        print("✅ Benchmark Suite Completed!")
        return suite_results


# Example usage and demo functions
async def demo_performance_monitoring():
    """Demonstrate the performance monitoring system."""
    print("📊 Performance Monitoring Demo")
    print("=" * 50)
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Record some sample metrics
    monitor.record_metric("startup_time", 1.234, "seconds", {"component": "main"})
    monitor.record_metric("memory_usage", 45.6, "MB", {"process": "downloader"})
    
    # Get system metrics
    system_metrics = monitor.get_system_metrics()
    print("🖥️ Current System Metrics:")
    print(json.dumps(system_metrics, indent=2))
    
    # Run automated benchmarks
    benchmarks = AutomatedBenchmarks(monitor)
    await benchmarks.run_full_benchmark_suite()
    
    # Get performance summary
    summary = monitor.get_performance_summary()
    print("\n📈 Performance Summary:")
    print(json.dumps(summary, indent=2))
    
    # Export metrics
    metrics_json = monitor.export_metrics_json()
    print(f"\n💾 Exported metrics ({len(metrics_json)} characters)")
    
    return monitor


if __name__ == "__main__":
    # Run demo if script is executed directly
    asyncio.run(demo_performance_monitoring())