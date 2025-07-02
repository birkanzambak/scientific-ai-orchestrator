#!/usr/bin/env python3
"""
Performance Dashboard for Scientific AI Orchestrator
----------------------------------------------------

Generates performance reports and visualizations from monitoring data.
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.monitoring import PerformanceMonitor
from utils.statistical_analysis import StatisticalAnalyzer

def generate_performance_report(hours: int = 24, output_file: str = None) -> str:
    """Generate a comprehensive performance report."""
    monitor = PerformanceMonitor()
    summary = monitor.get_performance_summary(hours)
    
    if "message" in summary:
        return f"# Performance Report\n\n{summary['message']}"
    
    report = f"""
# Scientific AI Orchestrator - Performance Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Time Period**: Last {hours} hours

## Executive Summary

- **Total Pipelines**: {summary['total_pipelines']}
- **Success Rate**: {summary['success_rate']:.1f}%
- **Total Cost**: ${summary['total_cost']:.4f}
- **Average Cost per Pipeline**: ${summary['average_cost_per_pipeline']:.4f}
- **Total Duration**: {summary['total_duration']:.1f} seconds
- **Average Duration per Pipeline**: {summary['average_duration_per_pipeline']:.1f} seconds

## Agent Performance

"""
    
    for agent_name, stats in summary.get('agent_statistics', {}).items():
        success_rate = (stats['successful_runs'] / stats['total_runs'] * 100) if stats['total_runs'] > 0 else 0
        avg_duration = stats['total_duration'] / stats['total_runs'] if stats['total_runs'] > 0 else 0
        avg_cost = stats['total_cost'] / stats['total_runs'] if stats['total_runs'] > 0 else 0
        
        report += f"""
### {agent_name.title()}
- **Total Runs**: {stats['total_runs']}
- **Success Rate**: {success_rate:.1f}%
- **Average Duration**: {avg_duration:.2f}s
- **Average Cost**: ${avg_cost:.4f}
- **Total Cost**: ${stats['total_cost']:.4f}

"""
    
    report += """
## Recommendations

"""
    
    if summary['success_rate'] < 90:
        report += "- **Low Success Rate**: Consider reviewing error logs and improving error handling\n"
    
    if summary['average_cost_per_pipeline'] > 0.1:
        report += "- **High Cost**: Consider using cheaper models for initial processing\n"
    
    if summary['average_duration_per_pipeline'] > 60:
        report += "- **Slow Performance**: Consider optimizing pipeline or using faster models\n"
    
    report += """
## System Health

"""
    
    if summary['success_rate'] >= 95:
        report += "- ✅ **Excellent**: System performing well\n"
    elif summary['success_rate'] >= 85:
        report += "- ⚠️ **Good**: Minor issues detected\n"
    elif summary['success_rate'] >= 70:
        report += "- ⚠️ **Fair**: Some issues need attention\n"
    else:
        report += "- ❌ **Poor**: Significant issues detected\n"
    
    if summary['average_duration_per_pipeline'] < 30:
        report += "- ✅ **Fast**: Response times are excellent\n"
    elif summary['average_duration_per_pipeline'] < 60:
        report += "- ⚠️ **Acceptable**: Response times are reasonable\n"
    else:
        report += "- ❌ **Slow**: Response times need improvement\n"
    
    report = report.strip()
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to {output_file}")
    
    return report

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='Generate performance reports')
    parser.add_argument('--hours', type=int, default=24, help='Hours to analyze (default: 24)')
    parser.add_argument('--output', type=str, help='Output file for report')
    
    args = parser.parse_args()
    report = generate_performance_report(args.hours, args.output)
    print(report)

if __name__ == "__main__":
    main()
