"""
Performance monitoring and logging utilities for Scientific AI Orchestrator
---------------------------------------------------------------------------

Provides comprehensive monitoring, logging, and performance tracking for the AI pipeline.
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    agent_name: str
    start_time: float
    end_time: float
    success: bool
    error_message: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_estimate: Optional[float] = None
    
    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def cost_per_second(self) -> Optional[float]:
        """Cost per second if cost is available."""
        if self.cost_estimate and self.duration > 0:
            return self.cost_estimate / self.duration
        return None

@dataclass
class PipelineMetrics:
    """Complete pipeline execution metrics."""
    task_id: str
    question: str
    start_time: float
    end_time: float
    success: bool
    agent_metrics: List[AgentMetrics]
    total_cost: float = 0.0
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Total pipeline duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        """Success rate of individual agents."""
        if not self.agent_metrics:
            return 0.0
        successful = sum(1 for m in self.agent_metrics if m.success)
        return (successful / len(self.agent_metrics)) * 100

class PerformanceMonitor:
    """Monitor for tracking pipeline performance and costs."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_pipeline: Optional[PipelineMetrics] = None
        self.agent_metrics: List[AgentMetrics] = []
        
        # Performance thresholds
        self.cost_threshold = 1.0  # USD
        self.duration_threshold = 300  # seconds
        self.error_threshold = 0.2  # 20% error rate
    
    def start_pipeline(self, task_id: str, question: str) -> None:
        """Start monitoring a new pipeline execution."""
        self.current_pipeline = PipelineMetrics(
            task_id=task_id,
            question=question,
            start_time=time.time(),
            end_time=0.0,
            success=False,
            agent_metrics=[]
        )
        self.agent_metrics = []
        logger.info(f"Started pipeline monitoring for task {task_id}")
    
    def start_agent(self, agent_name: str) -> str:
        """Start monitoring an agent execution. Returns metric ID."""
        metric_id = f"{agent_name}_{int(time.time() * 1000)}"
        metric = AgentMetrics(
            agent_name=agent_name,
            start_time=time.time(),
            end_time=0.0,
            success=False
        )
        self.agent_metrics.append(metric)
        logger.info(f"Started {agent_name} execution")
        return metric_id
    
    def end_agent(self, metric_id: str, success: bool, 
                  error_message: Optional[str] = None,
                  input_tokens: Optional[int] = None,
                  output_tokens: Optional[int] = None,
                  cost_estimate: Optional[float] = None) -> None:
        """End monitoring an agent execution."""
        metric = self.agent_metrics[-1]  # Assume last started agent
        metric.end_time = time.time()
        metric.success = success
        metric.error_message = error_message
        metric.input_tokens = input_tokens
        metric.output_tokens = output_tokens
        metric.cost_estimate = cost_estimate
        
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Ended {metric.agent_name} execution: {status} ({metric.duration:.2f}s)")
        
        if cost_estimate:
            logger.info(f"{metric.agent_name} cost: ${cost_estimate:.4f}")
    
    def end_pipeline(self, success: bool, error_message: Optional[str] = None) -> PipelineMetrics:
        """End monitoring a pipeline execution."""
        if not self.current_pipeline:
            raise ValueError("No pipeline currently being monitored")
        
        self.current_pipeline.end_time = time.time()
        self.current_pipeline.success = success
        self.current_pipeline.error_message = error_message
        self.current_pipeline.agent_metrics = self.agent_metrics.copy()
        
        # Calculate total cost
        total_cost = sum(m.cost_estimate or 0 for m in self.agent_metrics)
        self.current_pipeline.total_cost = total_cost
        
        # Log pipeline completion
        logger.info(f"Pipeline completed: {success} ({self.current_pipeline.duration:.2f}s, ${total_cost:.4f})")
        
        # Save metrics
        self._save_metrics(self.current_pipeline)
        
        # Check for performance issues
        self._check_performance_issues(self.current_pipeline)
        
        return self.current_pipeline
    
    def _save_metrics(self, metrics: PipelineMetrics) -> None:
        """Save metrics to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pipeline_metrics_{timestamp}_{metrics.task_id}.json"
        filepath = self.log_dir / filename
        
        # Convert to dict for JSON serialization
        metrics_dict = asdict(metrics)
        
        with open(filepath, 'w') as f:
            json.dump(metrics_dict, f, indent=2, default=str)
        
        logger.info(f"Saved metrics to {filepath}")
    
    def _check_performance_issues(self, metrics: PipelineMetrics) -> None:
        """Check for performance issues and log warnings."""
        issues = []
        
        if metrics.total_cost > self.cost_threshold:
            issues.append(f"High cost: ${metrics.total_cost:.4f} > ${self.cost_threshold}")
        
        if metrics.duration > self.duration_threshold:
            issues.append(f"Slow execution: {metrics.duration:.2f}s > {self.duration_threshold}s")
        
        if metrics.success_rate < (1 - self.error_threshold) * 100:
            issues.append(f"High error rate: {100 - metrics.success_rate:.1f}% > {self.error_threshold * 100}%")
        
        if issues:
            logger.warning(f"Performance issues detected: {'; '.join(issues)}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours."""
        cutoff_time = time.time() - (hours * 3600)
        
        # Load metrics from files
        metrics_files = list(self.log_dir.glob("pipeline_metrics_*.json"))
        recent_metrics = []
        
        for filepath in metrics_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if data.get('start_time', 0) > cutoff_time:
                        recent_metrics.append(data)
            except Exception as e:
                logger.error(f"Error loading metrics from {filepath}: {e}")
        
        if not recent_metrics:
            return {"message": "No recent metrics found"}
        
        # Calculate summary statistics
        total_pipelines = len(recent_metrics)
        successful_pipelines = sum(1 for m in recent_metrics if m.get('success', False))
        total_cost = sum(m.get('total_cost', 0) for m in recent_metrics)
        total_duration = sum(m.get('duration', 0) for m in recent_metrics)
        
        # Agent-specific statistics
        agent_stats = {}
        for metrics in recent_metrics:
            for agent_metric in metrics.get('agent_metrics', []):
                agent_name = agent_metric.get('agent_name', 'unknown')
                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {
                        'total_runs': 0,
                        'successful_runs': 0,
                        'total_duration': 0,
                        'total_cost': 0
                    }
                
                agent_stats[agent_name]['total_runs'] += 1
                if agent_metric.get('success', False):
                    agent_stats[agent_name]['successful_runs'] += 1
                agent_stats[agent_name]['total_duration'] += agent_metric.get('duration', 0)
                agent_stats[agent_name]['total_cost'] += agent_metric.get('cost_estimate', 0)
        
        return {
            'time_period_hours': hours,
            'total_pipelines': total_pipelines,
            'successful_pipelines': successful_pipelines,
            'success_rate': (successful_pipelines / total_pipelines * 100) if total_pipelines > 0 else 0,
            'total_cost': total_cost,
            'average_cost_per_pipeline': total_cost / total_pipelines if total_pipelines > 0 else 0,
            'total_duration': total_duration,
            'average_duration_per_pipeline': total_duration / total_pipelines if total_pipelines > 0 else 0,
            'agent_statistics': agent_stats
        }

class AdaptiveConfig:
    """Adaptive configuration based on performance monitoring."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.base_config = {
            'sophia': {'model': 'gpt-4o-mini', 'max_retries': 3},
            'nova': {'max_results': 10, 'model': 'gpt-4o-mini'},
            'lyra': {'model': 'gpt-4o', 'cost_threshold': 0.05},
            'critic': {'model': 'gpt-4o-mini', 'max_retries': 2}
        }
    
    def get_adaptive_config(self, agent_name: str) -> Dict[str, Any]:
        """Get adaptive configuration for an agent based on performance."""
        summary = self.monitor.get_performance_summary(hours=1)  # Last hour
        
        if not summary or 'agent_statistics' not in summary:
            return self.base_config.get(agent_name, {})
        
        agent_stats = summary['agent_statistics'].get(agent_name, {})
        
        if not agent_stats:
            return self.base_config.get(agent_name, {})
        
        # Adaptive logic based on performance
        success_rate = (agent_stats['successful_runs'] / agent_stats['total_runs'] * 100) if agent_stats['total_runs'] > 0 else 100
        avg_cost = agent_stats['total_cost'] / agent_stats['total_runs'] if agent_stats['total_runs'] > 0 else 0
        
        config = self.base_config.get(agent_name, {}).copy()
        
        # Adjust model based on cost and success rate
        if avg_cost > 0.1 and success_rate > 90:  # High cost but good success
            if 'model' in config and config['model'] == 'gpt-4o':
                config['model'] = 'gpt-4o-mini'
                logger.info(f"Adaptive config: Switched {agent_name} to gpt-4o-mini due to high cost")
        
        # Adjust retries based on success rate
        if success_rate < 80:
            config['max_retries'] = config.get('max_retries', 3) + 1
            logger.info(f"Adaptive config: Increased {agent_name} retries due to low success rate")
        
        return config
