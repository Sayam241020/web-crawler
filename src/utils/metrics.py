"""
Performance metrics collection and reporting
"""
import time
import psutil
import os
import json
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import numpy as np


class MetricsCollector:
    """Collect and report performance metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.process = psutil.Process(os.getpid())
    
    def collect_index_metrics(self, index, index_name: str):
        """
        Collect metrics from an index
        
        Args:
            index: Index object
            index_name: Name of the index
        """
        self.metrics[index_name] = index.get_metrics()
        
        # Add memory usage
        mem_info = self.process.memory_info()
        self.metrics[index_name]['memory_rss_mb'] = mem_info.rss / (1024 * 1024)
    
    def get_latency_percentiles(self, query_times: List[float]) -> Dict[str, float]:
        """
        Calculate latency percentiles
        
        Args:
            query_times: List of query execution times
            
        Returns:
            Dictionary with p50, p95, p99 percentiles
        """
        if not query_times:
            return {'p50': 0, 'p95': 0, 'p99': 0}
        
        sorted_times = sorted(query_times)
        n = len(sorted_times)
        
        return {
            'p50': sorted_times[int(0.50 * n)] if n > 0 else 0,
            'p95': sorted_times[int(0.95 * n)] if n > 0 else 0,
            'p99': sorted_times[int(0.99 * n)] if n > 0 else 0
        }
    
    def calculate_throughput(self, num_operations: int, total_time: float) -> float:
        """
        Calculate throughput (operations per second)
        
        Args:
            num_operations: Number of operations performed
            total_time: Total time taken
            
        Returns:
            Throughput in operations/second
        """
        return num_operations / total_time if total_time > 0 else 0
    
    def save_metrics(self, output_path: str):
        """
        Save metrics to JSON file
        
        Args:
            output_path: Path to save metrics
        """
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def plot_latency_comparison(self, output_path: str):
        """
        Plot latency comparison across indexes
        
        Args:
            output_path: Path to save plot
        """
        if not self.metrics:
            return
        
        index_names = list(self.metrics.keys())
        p95_times = [self.metrics[name].get('p95_query_time', 0) * 1000 for name in index_names]
        p99_times = [self.metrics[name].get('p99_query_time', 0) * 1000 for name in index_names]
        
        x = np.arange(len(index_names))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(x - width/2, p95_times, width, label='P95')
        ax.bar(x + width/2, p99_times, width, label='P99')
        
        ax.set_xlabel('Index')
        ax.set_ylabel('Latency (ms)')
        ax.set_title('Query Latency Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(index_names, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    
    def plot_memory_comparison(self, output_path: str):
        """
        Plot memory usage comparison
        
        Args:
            output_path: Path to save plot
        """
        if not self.metrics:
            return
        
        index_names = list(self.metrics.keys())
        memory_usage = [self.metrics[name].get('memory_usage_mb', 0) for name in index_names]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(index_names, memory_usage)
        
        ax.set_xlabel('Index')
        ax.set_ylabel('Memory Usage (MB)')
        ax.set_title('Memory Footprint Comparison')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    
    def plot_throughput_comparison(self, throughput_data: Dict[str, float], output_path: str):
        """
        Plot throughput comparison
        
        Args:
            throughput_data: Dictionary of index_name -> throughput
            output_path: Path to save plot
        """
        if not throughput_data:
            return
        
        index_names = list(throughput_data.keys())
        throughputs = list(throughput_data.values())
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(index_names, throughputs)
        
        ax.set_xlabel('Index')
        ax.set_ylabel('Throughput (queries/sec)')
        ax.set_title('Query Throughput Comparison')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    
    def generate_report(self, output_dir: str):
        """
        Generate comprehensive metrics report
        
        Args:
            output_dir: Directory to save report files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON metrics
        self.save_metrics(os.path.join(output_dir, 'metrics.json'))
        
        # Generate plots
        self.plot_latency_comparison(os.path.join(output_dir, 'latency_comparison.png'))
        self.plot_memory_comparison(os.path.join(output_dir, 'memory_comparison.png'))
        
        print(f"Metrics report generated in {output_dir}")
